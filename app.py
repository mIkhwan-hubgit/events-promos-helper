from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import requests
import clock
import db
import json
from urllib.parse import quote_plus
from events import concerts_to_events, to_promo
from fetcher import fetch_cloudjoi_events, fetch_feed_text, fetch_ical_events, fetch_jsonld_events, fetch_text
from llm import classify_events, extract_promos, pick_tech_events, extract_concerts
from sources import SOURCES

FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}
EVENT_FETCHERS = {"ical": fetch_ical_events, "jsonld": fetch_jsonld_events, "cloudjoi": fetch_cloudjoi_events}
EMPTY_IS_NORMAL = set(EVENT_FETCHERS) | {"concert_page"}  # sources where finding nothing isn't a failure
COOLDOWN_HOURS = 6
CATEGORIES = {
    "bookstore_promo": "📚 Books",
    "tech_event": "💻 Tech events",
    "orchestra": "🎻 Orchestra & classical",
    "workshop": "🎨 Workshops",
    "video_games": "🎮 Video games",    
}
CHANNEL_LABELS = {"in_store": "In store", "online": "Online", "both": "In store & online"}

st.set_page_config(page_title="What's On Malaysia", page_icon="📚", layout="wide")
st.title("🗓️ What's On Malaysia")


def sources_for(category):
    return [s for s in SOURCES if category in s.get("categories", [s["category"]])]


def process_source(source):
    if source["type"] == "concert_page":
          try:
              text, _ = fetch_text(source["url"])
          except requests.HTTPError as e:
              if e.response is not None and e.response.status_code == 404:
                  return []  # next season's page isn't published yet
              raise
          concerts = extract_concerts(source["name"], text)
          return [to_promo(e) for e in concerts_to_events(concerts, source["url"], source["venue"])]
    if source["type"] in EVENT_FETCHERS:
        events = EVENT_FETCHERS[source["type"]](source["url"])
        if source.get("region"):
            events = [e for e in events if source["region"] in f"{e['location'] or ''} {e['description']}"]
        if source.get("tech_filter"):
            events = pick_tech_events(events, source["name"])
        if source.get("classify"):
            events = classify_events(events, source["name"])
        return [to_promo(e) for e in events]
    text, images = FETCHERS[source["type"]](source["url"])
    return extract_promos(source["name"], text, images)


def refresh(category):
    sources = sources_for(category)
    if not sources:
        return ["No sources are set up for this tab yet."]

    # Start every source for this tab at the same time
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        jobs = [(source, pool.submit(process_source, source)) for source in sources]

    # All sources are finished by here; save the results one by one
    problems = []
    conn = db.connect()
    run_time = None
    seen_links = set()
    for source, job in jobs:
        try:
            promos = job.result()
        except Exception as e:
            problems.append(f"Couldn't update {source['name']}: {e}")
            continue
        if not promos:
            if source["type"] not in EMPTY_IS_NORMAL:
                problems.append(f"{source['name']}: nothing found this time. The model may have failed, so previously saved results are kept.")
            continue
        if run_time is None:
            run_time = db.start_refresh(conn, category)  # only count the refresh once a source actually worked
        for p in promos:
            row = p.model_dump(mode="json")
            row["category"] = row.get("category") or source["category"]
            if row["category"] != category:
                continue  # belongs to another tab; saved when that tab is refreshed (from cache, no extra quota)
            if source["type"] in EVENT_FETCHERS:
                if p.link and p.link in seen_links:
                    continue  # same event already saved from another feed in this refresh
                seen_links.add(p.link)
            row.setdefault("topic", None)  # bookstore promos have no topic
            row["source"] = source["name"]
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

def show_category(category, df, show_expired, window):
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

    st.dataframe(
        rows[columns],
        hide_index=True,
        column_config={
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
        },
    )


conn = db.connect()
df = pd.DataFrame(db.load_promos(conn))
conn.close()

left, right = st.columns([3, 1])
with left:
    when = st.radio("When", ["Any time", "This weekend", "Next 7 days"], horizontal=True)
with right:
    show_expired = st.checkbox("Show expired")
window = date_window(when, clock.today())

tabs = st.tabs(list(CATEGORIES.values()))
for tab, category in zip(tabs, CATEGORIES):
    with tab:
        if category == "video_games":
            show_watchlist()
        else:
            show_category(category, df, show_expired, window)

with st.expander("ℹ️ How this works"):
    st.markdown("""
- **Sources:** bookstore promo pages and feeds (POPULAR, Kinokuniya, BookXcess, Big Bad Wolf), tech event calendars (Luma, dev.events), and CloudJoi for concerts and workshops.
- **Structured data is read with plain code:** event feeds already have exact dates, times and venues.
- **An LLM (Gemini) is used only where judgement is needed:** reading messy promo pages and banner images, and deciding which events belong in which tab.
- **Every answer is cached,** so unchanged pages never use API quota twice.
- **Accuracy is measured** against hand-labelled test sets: 100% recall and precision on 29 bookstore promos, and on 13 events for the tech filter.
""")