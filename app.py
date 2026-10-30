from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import clock
import db
from events import to_promo
from fetcher import fetch_feed_text, fetch_ical_events, fetch_text
from llm import extract_promos, pick_tech_events
from sources import SOURCES

FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}
COOLDOWN_HOURS = 6
CATEGORIES = {
    "bookstore_promo": "📚 Bookstore promos",
    "tech_event": "💻 Tech events",
}

st.set_page_config(page_title="Promo & Event Tracker", page_icon="📚", layout="wide")
st.title("📚 Malaysia Bookstore Promos & Tech Events")


def process_source(source):
    if source["type"] == "ical":
        events = fetch_ical_events(source["url"])
        if source.get("tech_filter"):
            events = pick_tech_events(events, source["name"])
        return [to_promo(e) for e in events]
    text, images = FETCHERS[source["type"]](source["url"])
    return extract_promos(source["name"], text, images)


def refresh(category):
    sources = [s for s in SOURCES if s["category"] == category]

    # Start every source in this category at the same time
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        jobs = [(source, pool.submit(process_source, source)) for source in sources]

    # All sources are finished by here; save the results one by one
    problems = []
    conn = db.connect()
    run_time = db.start_refresh(conn, category)
    for source, job in jobs:
        try:
            promos = job.result()
        except Exception as e:
            problems.append(f"Couldn't update {source['name']}: {e}")
            continue
        if not promos:
            if source["type"] != "ical":  # an empty event calendar is normal, not a failure
                problems.append(f"{source['name']}: nothing found this time. The model may have failed, so previously saved results are kept.")
            continue
        for p in promos:
            row = p.model_dump(mode="json")
            row["source"] = source["name"]
            row["category"] = source["category"]
            row["link"] = p.link or source["url"]
            db.save_promo(conn, row, run_time)
    conn.commit()
    conn.close()
    return problems


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None  # missing or badly formatted date


def status(row, info, today):
    if info["count"] > 1 and row["first_seen"] == info["latest"]:
        return "🆕 New"
    if row["category"] == "tech_event":
        start = parse_date(row["start_date"])
        if start:
            days = (start - today).days
            if days == 0:
                return "📅 Today"
            if 0 < days <= 3:
                return f"📅 In {days} days"
        return ""
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


def show_category(category, df, show_expired):
    conn = db.connect()
    info = db.refresh_info(conn, category)
    conn.close()

    too_soon = bool(info["latest"]) and (
        clock.now() - clock.parse(info["latest"]) < timedelta(hours=COOLDOWN_HOURS)
    )
    if st.button("🔄 Refresh", key=f"refresh_{category}", type="primary", disabled=too_soon):
        with st.spinner("Checking sources..."):
            st.session_state[f"problems_{category}"] = refresh(category)
        st.rerun()  # redraw the page so the cooldown applies straight away
    if too_soon:
        st.caption(f"Refresh is limited to once every {COOLDOWN_HOURS} hours to protect the free API quota and the websites.")
    for message in st.session_state.get(f"problems_{category}", []):
        st.warning(message)

    if info["count"] == 0:
        st.info("Press Refresh to load the latest results.")
        return
    st.caption(f"Last refreshed: {clock.parse(info['latest']):%d %b %Y, %I:%M %p}")

    rows = df[df["category"] == category].copy() if not df.empty else pd.DataFrame()
    if rows.empty:
        st.write("Nothing found yet.")
        return

    today = clock.today()
    rows["status"] = rows.apply(lambda r: status(r, info, today), axis=1)
    if not show_expired:
        still_running = rows["end_date"].isna() | (rows["end_date"] >= today.isoformat())
        # items with no end date disappear once they haven't been seen for 30 days
        stale_cutoff = (clock.now() - timedelta(days=30)).isoformat()
        recently_seen = rows["end_date"].notna() | (rows["last_seen"] >= stale_cutoff)
        rows = rows[still_running & recently_seen]
    if rows.empty:
        st.write("Nothing current right now.")
        return

    if category == "tech_event":
        rows = rows.sort_values("start_date")
        columns = ["status", "source", "title", "details", "location", "link"]
    else:
        rows = rows.sort_values("end_date", na_position="last")  # ending soonest first
        columns = ["status", "source", "title", "details", "start_date", "end_date", "location", "channel", "link"]

    st.dataframe(
        rows[columns],
        hide_index=True,
        column_config={
            "status": st.column_config.TextColumn("Status", width="medium"),
            "link": st.column_config.LinkColumn("Link", display_text="Open"),
        },
    )


conn = db.connect()
df = pd.DataFrame(db.load_promos(conn))
conn.close()

show_expired = st.checkbox("Show expired")
tabs = st.tabs(list(CATEGORIES.values()))
for tab, category in zip(tabs, CATEGORIES):
    with tab:
        show_category(category, df, show_expired)