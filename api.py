"""Web API for the new What's On Malaysia website.

The React website asks this for events. All the fetching, Gemini calls and saving
still happen in Python, exactly as in the Streamlit app.
"""
import hashlib
import hmac
import json
import os
import threading
import time
from datetime import timedelta
from typing import Literal
from urllib.parse import quote_plus

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import clock
import db
from pipeline import CATEGORIES, COOLDOWN_HOURS, refresh

load_dotenv()  # reads PLANS_PASSWORD (and the Gemini settings) from .env

app = FastAPI(title="What's On Malaysia API")

# The website lives at a different address, so allow it to call us.
# On your computer that's localhost:3000; online, ALLOWED_ORIGINS holds the Vercel address.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT"],
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
def refresh_category(category: str, authorization: str | None = Header(default=None)):
    # Everyone gets the daily 6 a.m. refresh; refreshing by hand is only for you (unlocked)
    require_owner(authorization)
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



# ---------- Private plans (Want / Going) ----------
# Only someone who knows PLANS_PASSWORD can see or change plans. After a correct password,
# the website gets a "token": an expiry time plus a signature only this server can make.
# Leave PLANS_PASSWORD unset and plans are switched off entirely.

PLANS_PASSWORD = os.getenv("PLANS_PASSWORD")
TOKEN_DAYS = 30
MAX_FAILED_LOGINS = 5  # per visitor, per 15 minutes
failed_logins: dict[str, list[float]] = {}


def sign(expiry: str) -> str:
    key = (PLANS_PASSWORD or "").encode()
    return hmac.new(key, f"plans:{expiry}".encode(), hashlib.sha256).hexdigest()


def require_owner(authorization: str | None = Header(default=None)):
    """Stops the request unless it carries a valid, unexpired token."""
    if not PLANS_PASSWORD:
        raise HTTPException(status_code=404, detail="Plans are switched off on this site.")
    token = (authorization or "").removeprefix("Bearer ").strip()
    expiry, _, signature = token.partition(".")
    if not expiry.isdigit() or int(expiry) < time.time() or not hmac.compare_digest(signature, sign(expiry)):
        raise HTTPException(status_code=401, detail="Please unlock your plans again.")


class Login(BaseModel):
    password: str


@app.post("/api/login")
def login(body: Login, request: Request):
    if not PLANS_PASSWORD:
        raise HTTPException(status_code=404, detail="Plans are switched off on this site.")
    visitor = request.client.host if request.client else "unknown"
    recent = [t for t in failed_logins.get(visitor, []) if t > time.time() - 15 * 60]
    if len(recent) >= MAX_FAILED_LOGINS:
        raise HTTPException(status_code=429, detail="Too many wrong passwords. Try again in 15 minutes.")
    if not hmac.compare_digest(body.password.encode(), PLANS_PASSWORD.encode()):
        failed_logins[visitor] = recent + [time.time()]
        raise HTTPException(status_code=401, detail="Wrong password.")
    failed_logins.pop(visitor, None)
    expiry = str(int(time.time()) + TOKEN_DAYS * 24 * 3600)
    return {"token": f"{expiry}.{sign(expiry)}"}


@app.get("/api/plans", dependencies=[Depends(require_owner)])
def get_plans():
    conn = db.connect()
    plans = db.load_plans(conn)
    conn.close()
    return plans


class PlanChange(BaseModel):
    source: str
    title_key: str
    status: Literal["want", "going"] | None  # None removes the plan
    category: str | None = None
    title: str | None = None
    start_date: str | None = None
    link: str | None = None


@app.put("/api/plans", dependencies=[Depends(require_owner)])
def change_plan(change: PlanChange):
    conn = db.connect()
    db.set_plan(conn, change.model_dump(exclude={"status"}), change.status)
    conn.commit()
    conn.close()
    return {"ok": True}