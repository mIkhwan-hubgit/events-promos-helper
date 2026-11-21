"""Collects events and promos from every source and saves them.

Shared by the Streamlit app (app.py) and the web API (api.py).
"""
from concurrent.futures import ThreadPoolExecutor

import requests

import db
from events import concerts_to_events, to_promo
from fetcher import (fetch_cloudjoi_events, fetch_feed_text, fetch_ical_events, fetch_jsonld_events,
                     fetch_klec_events, fetch_mwo_events, fetch_text)
from llm import classify_events, extract_concerts, extract_promos, pick_tech_events
from sources import SOURCES

FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}
EVENT_FETCHERS = {"ical": fetch_ical_events, "jsonld": fetch_jsonld_events, "cloudjoi": fetch_cloudjoi_events,
                  "mwo": fetch_mwo_events, "klec": fetch_klec_events}
EMPTY_IS_NORMAL = set(EVENT_FETCHERS) | {"concert_page"}  # sources where finding nothing isn't a failure
COOLDOWN_HOURS = 6
CATEGORIES = {
    "bookstore_promo": "📚 Books",
    "tech_event": "💻 Tech events",
    "orchestra": "🎻 Orchestra & classical",
    "workshop": "🎨 Workshops",
    "video_games": "🎮 Video games",
}

def safe_link(link):
    """Only keep normal web links. Text read from other websites (and the LLM's answers about it) is
    untrusted, so a "javascript:" or other odd link is dropped and the source's own page is used instead."""
    if link and link.strip().lower().startswith(("https://", "http://")):
        return link.strip()
    return None

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
            row["link"] = safe_link(p.link) or source["url"]
            db.save_promo(conn, row, run_time)
    conn.commit()
    conn.close()
    return problems