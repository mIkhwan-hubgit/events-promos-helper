from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

import db
from fetcher import fetch_text, fetch_feed_text
from llm import extract_promos
from sources import SOURCES
from concurrent.futures import ThreadPoolExecutor

FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}

st.set_page_config(page_title="Bookstore Promo Tracker", page_icon="📚", layout="wide")
st.title("📚 Malaysia Bookstore Promo Tracker")


def process_source(source):
    text = FETCHERS[source["type"]](source["url"])
    return extract_promos(source["name"], text)


def refresh():
    # Start every store at the same time
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        jobs = [(source, pool.submit(process_source, source)) for source in SOURCES]

    # All stores are finished by here; save the results one by one
    conn = db.connect()
    run_time = db.start_refresh(conn)
    for source, job in jobs:
        try:
            promos = job.result()
        except Exception as e:
            st.warning(f"Couldn't update {source['name']}: {e}")
            continue
        for p in promos:
            row = p.model_dump()
            row["source"] = source["name"]
            row["category"] = source["category"]
            row["link"] = p.link or source["url"]
            db.save_promo(conn, row, run_time)
    conn.commit()
    conn.close()


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None  # missing or badly formatted date


if st.button("🔄 Refresh", type="primary"):
    with st.spinner("Checking bookstores..."):
        refresh()

conn = db.connect()
info = db.refresh_info(conn)
df = pd.DataFrame(db.load_promos(conn))
conn.close()

if info["count"] == 0:
    st.info("Press Refresh to load the latest promotions.")
    st.stop()

latest = info["latest"]
st.caption(f"Last refreshed: {datetime.fromisoformat(latest):%d %b %Y, %I:%M %p}")

if df.empty:
    st.write("No promotions found.")
    st.stop()

today = date.today()


def status(row):
    if info["count"] > 1 and row["first_seen"] == latest:
        return "🆕 New"
    end = parse_date(row["end_date"])
    if end:
        days_left = (end - today).days
        if days_left < 0:
            return "Expired"
        if days_left == 0:
            return "⏰ Ends today"
        if days_left <= 3:
            return f"⏰ Ends in {days_left} days"
    return ""


df["status"] = df.apply(status, axis=1)

if not st.checkbox("Show expired"):
    still_running = df["end_date"].isna() | (df["end_date"] >= today.isoformat())
    # promos with no end date disappear once they haven't been seen for 30 days
    stale_cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    recently_seen = df["end_date"].notna() | (df["last_seen"] >= stale_cutoff)
    df = df[still_running & recently_seen]

df = df.sort_values("end_date", na_position="last")

st.dataframe(
    df[["status", "source", "title", "details", "start_date", "end_date", "location", "channel", "link"]],
    hide_index=True,
    column_config={
           "status": st.column_config.TextColumn("Status", width="medium"),
           "link": st.column_config.LinkColumn("Link", display_text="Open"),
       },
)