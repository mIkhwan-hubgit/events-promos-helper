from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pipeline import CATEGORIES, COOLDOWN_HOURS, refresh

import pandas as pd
import streamlit as st

import requests
import clock
import db
import json
from urllib.parse import quote_plus
from events import concerts_to_events, to_promo
from fetcher import fetch_cloudjoi_events, fetch_feed_text, fetch_ical_events, fetch_jsonld_events, fetch_text, fetch_mwo_events, fetch_klec_events
from llm import classify_events, extract_promos, pick_tech_events, extract_concerts
from sources import SOURCES
import hmac
import os

from dotenv import load_dotenv
from streamlit_sortables import sort_items

load_dotenv()


CHANNEL_LABELS = {"in_store": "In store", "online": "Online", "both": "In store & online"}
PLAN_LABELS = {None: "—", "want": "⭐ Want", "going": "✅ Going"}
PLAN_CODES = {label: code for code, label in PLAN_LABELS.items()}

st.set_page_config(page_title="What's On Malaysia", page_icon="📚", layout="wide")
st.title("🗓️ What's On Malaysia")

def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None  # missing or badly formatted date


def status(row, info, today):
    if info["count"] > 1 and row["first_seen"] == info["latest"]:
        return "🆕 New"
    if row["category"] != "bookstore_promo":  # events: count down to the start
        start = parse_date(row["start_date"])
        if start:
            days = (start - today).days
            if days == 0:
                return "📅 Today"
            if days == 1:
                return "📅 Tomorrow"
            if 1 < days <= 3:
                return f"📅 In {days} days"
        return ""
    end = parse_date(row["end_date"])  # promos: count down to the end
    if end:
        days_left = (end - today).days
        if days_left < 0:
            return "Expired"
        if days_left == 0:
            return "⏰ Ends today"
        if days_left == 1:
            return "⏰ Ends tomorrow"
        if days_left <= 3:
            return f"⏰ Ends in {days_left} days"
    return ""


def date_window(choice, today):
    if choice == "This weekend":
        if today.weekday() == 6:  # Sunday: the weekend is just today
            return today, today
        saturday = today + timedelta(days=5 - today.weekday())
        return max(today, saturday), saturday + timedelta(days=1)
    if choice == "Next 7 days":
        return today, today + timedelta(days=6)
    return None  # any time

def show_watchlist():
    st.caption("There's no reliable automated source for video game events in Malaysia, "
               "so this is a list of events to check yourself.")
    try:
        with open("watchlist.json", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        st.info("Add events to watchlist.json to see them here.")
        return

    year = clock.today().year
    rows = pd.DataFrame([
        {
            "name": item["name"],
            "search": f"https://www.google.com/search?q={quote_plus(item['name'] + ' ' + str(year))}",
            "site": item.get("site"),
            "note": item.get("note", ""),
        }
        for item in items
    ])
    st.dataframe(
        rows,
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Event"),
            "search": st.column_config.LinkColumn("Search", display_text="Google it"),
            "site": st.column_config.LinkColumn("Official site", display_text="Open"),
            "note": st.column_config.TextColumn("Note"),
        },
    )

def lock_plans():
    st.session_state["owner"] = False


def is_owner():
    """True only in a browser tab where the plans password was typed in."""
    password = os.getenv("PLANS_PASSWORD")
    if not password:
        return False  # no password set: plans are switched off for everyone
    if st.session_state.get("owner"):
        st.sidebar.button("🔒 Lock my plans", on_click=lock_plans)
        return True
    attempt = st.sidebar.text_input("🔒 Password for my plans", type="password")
    if attempt and hmac.compare_digest(attempt, password):
        st.session_state["owner"] = True
        st.rerun()
    elif attempt:
        st.sidebar.error("Wrong password")
    return False


def plan_item(r):
    """The details of a table row that a plan needs to keep."""
    start = r["start_date"]
    return {
        "source": r["source"],
        "title_key": r["title_key"],
        "category": r["category"],
        "title": r["title"],
        "link": r["link"],
        "start_date": start.date().isoformat() if pd.notna(start) else None,
    }


def save_plans(changes):
    conn = db.connect()
    for item, status in changes:
        db.set_plan(conn, item, status)
    conn.commit()
    conn.close()
    st.session_state["plans_version"] = st.session_state.get("plans_version", 0) + 1  # redraw with saved plans
    st.rerun()


def show_plans():
    conn = db.connect()
    plans = db.load_plans(conn)
    conn.close()
    if not plans:
        st.info("Nothing planned yet. Use the My plan column in any tab to add events.")
        return

    by_label, lists = {}, {"want": [], "going": []}
    for p in plans:
        label = f"{p['title']} · {p['start_date'] or 'no date'} · {p['source']}"
        by_label[label] = p
        lists[p["status"]].append(label)

    st.caption("Drag events between the two lists. Changes save straight away.")
    board = sort_items(
        [{"header": "⭐ Want", "items": lists["want"]}, {"header": "✅ Going", "items": lists["going"]}],
        multi_containers=True,
        key=f"plans_board_{st.session_state.get('plans_version', 0)}",
    )
    moved = [
        (by_label[label], status)
        for container, status in zip(board, ["want", "going"])
        for label in container["items"]
        if by_label[label]["status"] != status
    ]
    if moved:
        save_plans(moved)

    st.dataframe(
        pd.DataFrame(plans)[["status", "start_date", "title", "source", "link"]],
        hide_index=True,
        column_config={
            "status": st.column_config.TextColumn("Plan"),
            "start_date": st.column_config.TextColumn("Starts"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "source": st.column_config.TextColumn("Source"),
            "link": st.column_config.LinkColumn("Link", display_text="Open"),
        },
    )
    remove = st.multiselect("Remove from my plans", list(by_label))
    if remove and st.button("Remove selected"):
        save_plans([(by_label[label], None) for label in remove])

def show_category(category, df, show_expired, window, owner=False):
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
    if window:
        # keep anything running at some point during the window
        window_start, window_end = (d.isoformat() for d in window)
        starts_in_time = rows["start_date"].isna() | (rows["start_date"] <= window_end)
        not_ended = rows["end_date"].isna() | (rows["end_date"] >= window_start)
        rows = rows[starts_in_time & not_ended]

    if category != "bookstore_promo":  # all event tabs
        if category == "tech_event":
            topics = sorted(rows["topic"].dropna().unique()) if "topic" in rows else []
            if topics:
                chosen = st.multiselect("Topics", topics, default=topics, key="topics")
                rows = rows[rows["topic"].isin(chosen) | rows["topic"].isna()]
        rows = rows.sort_values("start_date")
        rows["location"] = rows["location"].fillna("See event page")
        rows["start_date"] = pd.to_datetime(rows["start_date"], errors="coerce")  # a real date, so it sorts by date, not text
        columns = ["status"] + (["topic"] if category == "tech_event" else []) + ["start_date", "source", "title", "details", "location", "link"]
        soon_label = "Starting soon"
    else:
        rows = rows.sort_values("end_date", na_position="last")  # ending soonest first
        rows["location"] = rows["location"].fillna("—")
        rows["channel"] = rows["channel"].map(CHANNEL_LABELS).fillna("—")
        rows["start_date"] = pd.to_datetime(rows["start_date"], errors="coerce")
        rows["end_date"] = pd.to_datetime(rows["end_date"], errors="coerce")
        columns = ["status", "source", "title", "details", "start_date", "end_date", "location", "channel", "link"]
        soon_label = "Ending soon"
    rows["details"] = rows["details"].fillna("")

    if rows.empty:
        st.write("Nothing matches right now.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Showing", int(len(rows)))
    col2.metric("🆕 New", int((rows["status"] == "🆕 New").sum()))
    col3.metric(soon_label, int(rows["status"].str.startswith(("⏰", "📅")).sum()))

    config = {
        "status": st.column_config.TextColumn("Status", width="medium"),
        "topic": st.column_config.TextColumn("Topic"),
        "source": st.column_config.TextColumn("Source"),
        "title": st.column_config.TextColumn("Title", width="large"),
        "details": st.column_config.TextColumn("Details", width="large"),
        "start_date": st.column_config.DateColumn("Starts", format="D MMM YYYY"),
        "end_date": st.column_config.DateColumn("Ends", format="D MMM YYYY"),
        "location": st.column_config.TextColumn("Location"),
        "channel": st.column_config.TextColumn("Where"),
        "link": st.column_config.LinkColumn("Link", display_text="Open"),
        "plan": st.column_config.SelectboxColumn("My plan", options=list(PLAN_CODES), required=True),
    }
    if not owner:
        st.dataframe(rows[columns], hide_index=True, column_config=config)
        return

    # Only after the password: a "My plan" dropdown on every row
    conn = db.connect()
    saved = {(p["source"], p["title_key"]): p["status"] for p in db.load_plans(conn)}
    conn.close()
    rows["plan"] = [PLAN_LABELS[saved.get(key)] for key in zip(rows["source"], rows["title_key"])]
    edited = st.data_editor(
        rows[["plan"] + columns + ["title_key", "category"]],
        column_order=["plan"] + columns,
        disabled=columns,  # every column except "My plan" stays read-only
        hide_index=True,
        column_config=config,
        key=f"editor_{category}_{st.session_state.get('plans_version', 0)}",
    )
    changed = edited[edited["plan"] != rows["plan"]]
    if not changed.empty:
        save_plans([(plan_item(r), PLAN_CODES[r["plan"]]) for _, r in changed.iterrows()])


conn = db.connect()
df = pd.DataFrame(db.load_promos(conn))
conn.close()

left, right = st.columns([3, 1])
with left:
    when = st.radio("When", ["Any time", "This weekend", "Next 7 days"], horizontal=True)
with right:
    show_expired = st.checkbox("Show expired")
window = date_window(when, clock.today())

owner = is_owner()
tab_names = list(CATEGORIES.values()) + (["📌 My plans"] if owner else [])
tabs = st.tabs(tab_names)
for tab, category in zip(tabs, CATEGORIES):
    with tab:
        show_category(category, df, show_expired, window, owner)
        if category == "video_games":
            st.divider()
            st.subheader("Watchlist")
            show_watchlist()
if owner:
    with tabs[-1]:
        show_plans()

with st.expander("ℹ️ How this works"):
    st.markdown("""
- **Sources:** bookstore promo pages and feeds (POPULAR, Kinokuniya, BookXcess, Big Bad Wolf), tech event calendars (Luma, dev.events), and CloudJoi for concerts and workshops.
- **Structured data is read with plain code:** event feeds already have exact dates, times and venues.
- **An LLM (Gemini) is used only where judgement is needed:** reading messy promo pages and banner images, and deciding which events belong in which tab.
- **Every answer is cached,** so unchanged pages never use API quota twice.
- **Accuracy is measured** against hand-labelled test sets: 100% recall and precision on 29 bookstore promos, and on 13 events for the tech filter.
""")