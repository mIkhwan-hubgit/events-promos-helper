"""Web API for the new What's On Malaysia website.

The React website asks this for events. All the fetching, Gemini calls and saving
still happen in Python, exactly as in the Streamlit app.
"""
import json
import threading
from datetime import timedelta
from urllib.parse import quote_plus

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import clock
import db
from pipeline import CATEGORIES, COOLDOWN_HOURS, refresh

app = FastAPI(title="What's On Malaysia API")

# While developing, the website runs at localhost:3000, a different address, so allow it to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

refresh_lock = threading.Lock()  # stops two refreshes running at the same time


def check_category(category):
    if category not in CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Unknown category '{category}'")


def next_refresh_time(info):
    """When the cooldown ends, or None if a refresh is allowed now."""
    if not info["latest"]:
        return None
    allowed = clock.parse(info["latest"]) + timedelta(hours=COOLDOWN_HOURS)
    return allowed.isoformat() if allowed > clock.now() else None


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/categories")
def categories():
    return [{"id": key, "label": label} for key, label in CATEGORIES.items()]


@app.get("/api/events/{category}")
def events(category: str, show_expired: bool = False):
    check_category(category)
    conn = db.connect()
    info = db.refresh_info(conn, category)
    rows = [r for r in db.load_promos(conn) if r["category"] == category]
    conn.close()

    today = clock.today().isoformat()
    stale_cutoff = (clock.now() - timedelta(days=30)).isoformat()
    kept = []
    for r in rows:
        if not show_expired:
            if r["end_date"] and r["end_date"] < today:
                continue  # already over
            if not r["end_date"] and r["last_seen"] < stale_cutoff:
                continue  # no end date and not seen for 30 days
        r["is_new"] = info["count"] > 1 and r["first_seen"] == info["latest"]
        kept.append(r)
    kept.sort(key=lambda r: (r["start_date"] or "9999", r["title"]))
    return {
        "category": category,
        "refreshed_at": info["latest"],
        "next_refresh_at": next_refresh_time(info),
        "events": kept,
    }


@app.post("/api/refresh/{category}")
def refresh_category(category: str):
    check_category(category)
    conn = db.connect()
    info = db.refresh_info(conn, category)
    conn.close()
    wait_until = next_refresh_time(info)
    if wait_until:
        raise HTTPException(status_code=429, detail=f"Refresh is limited to once every {COOLDOWN_HOURS} hours. Next refresh: {wait_until}")
    if not refresh_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A refresh is already running. Try again in a minute.")
    try:
        problems = refresh(category)
    finally:
        refresh_lock.release()
    return {"category": category, "problems": problems}


@app.get("/api/watchlist")
def watchlist():
    try:
        with open("watchlist.json", encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return []
    year = clock.today().year
    return [
        {**item, "search": f"https://www.google.com/search?q={quote_plus(item['name'] + ' ' + str(year))}"}
        for item in items
    ]