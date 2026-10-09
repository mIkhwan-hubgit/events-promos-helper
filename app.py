from datetime import date, datetime

import pandas as pd
import streamlit as st

from fetcher import fetch_text, fetch_feed_text
from llm import extract_promos
from sources import SOURCES
FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}

st.set_page_config(page_title="Bookstore Promo Tracker", page_icon="📚", layout="wide")
st.title("📚 Malaysia Bookstore Promo Tracker")


def refresh():
    rows = []
    for source in SOURCES:
        try:
            text = FETCHERS[source["type"]](source["url"])
            promos = extract_promos(source["name"], text)
        except Exception as e:
            st.warning(f"Couldn't update {source['name']}: {e}")
            continue  # skip this store, keep going with the others
        for p in promos:
            row = p.model_dump()  # turn the Promo object into a dictionary
            row["source"] = source["name"]
            row["category"] = source["category"]
            row["link"] = p.link or source["url"]
            rows.append(row)
    st.session_state.promos = rows
    st.session_state.last_refreshed = datetime.now()


if st.button("🔄 Refresh", type="primary"):
    with st.spinner("Checking bookstores..."):
        refresh()

if "promos" not in st.session_state:
    st.info("Press Refresh to load the latest promotions.")
    st.stop()

st.caption(f"Last refreshed: {st.session_state.last_refreshed:%d %b %Y, %I:%M %p}")

df = pd.DataFrame(st.session_state.promos)
if df.empty:
    st.write("No promotions found.")
    st.stop()

today = date.today().isoformat()
if not st.checkbox("Show expired"):
    df = df[df["end_date"].isna() | (df["end_date"] >= today)]

df = df.sort_values("end_date", na_position="last")  # ending soonest first

st.dataframe(
    df[["source", "title", "details", "start_date", "end_date", "location", "channel", "link"]],
    hide_index=True,
    column_config={"link": st.column_config.LinkColumn("Link", display_text="Open")},
)