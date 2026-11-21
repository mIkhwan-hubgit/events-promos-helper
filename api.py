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
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, Field

import clock
import db
from pipeline import CATEGORIES, COOLDOWN_HOURS, refresh

load_dotenv()  # reads PLANS_PASSWORD (and the Gemini settings) from .env

# The automatic /docs pages list every endpoint; handy on your computer, not needed in public
SHOW_DOCS = os.getenv("SHOW_API_DOCS") == "1"
app = FastAPI(
    title="What's On Malaysia API",
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)

# The website lives at a different address, so allow it to call us.
# On your computer that's localhost:3000; online, ALLOWED_ORIGINS holds the Vercel address.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    # Everyone gets the daily morning refresh; refreshing by hand is only for you, the site owner
    if not is_owner(current_user(authorization)):
        raise HTTPException(status_code=403, detail="Only the site owner can refresh by hand. Everything refreshes every morning.")
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



# ---------- Accounts (Sign in with Google) and private plans ----------
# Google checks who someone is, so this site never sees or stores passwords.
# After Google says "this is really them", the site hands out its own "token": the person's
# Google ID plus an expiry time, signed with SESSION_SECRET so nobody can fake one.
# Without GOOGLE_CLIENT_ID and SESSION_SECRET, accounts are switched off.

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "").strip().lower()  # you: gets the Refresh button and your old plans
TOKEN_DAYS = 30
MAX_PLANS = 300  # per person: plenty for real use, stops anyone filling the database


def accounts_on():
    return bool(GOOGLE_CLIENT_ID and SESSION_SECRET)


def sign(text):
    return hmac.new(SESSION_SECRET.encode(), text.encode(), hashlib.sha256).hexdigest()


def make_token(user_id):
    expiry = int(time.time()) + TOKEN_DAYS * 24 * 3600
    payload = f"{user_id}.{expiry}"
    return f"{payload}.{sign(payload)}"


def user_id_from(authorization):
    """The Google ID inside a valid, unexpired token, or None."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    parts = token.split(".")
    if len(parts) != 3 or not parts[1].isdigit() or int(parts[1]) < time.time():
        return None
    payload = f"{parts[0]}.{parts[1]}"
    return parts[0] if hmac.compare_digest(parts[2], sign(payload)) else None


def current_user(authorization: str | None = Header(default=None)):
    """Stops the request unless it comes from someone who is signed in."""
    if not accounts_on():
        raise HTTPException(status_code=404, detail="Accounts are switched off on this site.")
    user_id = user_id_from(authorization)
    conn = db.connect()
    user = db.get_user(conn, user_id) if user_id else None
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return user


def is_owner(user):
    return bool(OWNER_EMAIL) and user["email"].lower() == OWNER_EMAIL


def public(user):
    """What the website may know about the signed-in person."""
    return {"name": user["name"], "email": user["email"], "is_owner": is_owner(user)}


class GoogleSignIn(BaseModel):
    credential: str  # the signed message Google gave the website


@app.post("/api/login/google")
def login_google(body: GoogleSignIn):
    if not accounts_on():
        raise HTTPException(status_code=404, detail="Accounts are switched off on this site.")
    try:
        # Checks Google's signature, that it was made for THIS site, and that it hasn't expired
        info = id_token.verify_oauth2_token(
            body.credential, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Google sign-in didn't work. Please try again.")
    if not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Your Google email isn't verified yet.")

    user_id = info["sub"]  # Google's ID for this person: never changes, unlike the email
    conn = db.connect()
    is_new = db.save_user(conn, user_id, info["email"], info.get("name"))
    user = db.get_user(conn, user_id)
    if is_new and is_owner(user):
        db.copy_old_plans(conn, user_id)  # your plans from before accounts existed
    conn.commit()
    conn.close()
    return {"token": make_token(user_id), "user": public(user)}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return public(user)


@app.delete("/api/me")
def delete_me(user=Depends(current_user)):
    conn = db.connect()
    db.delete_user(conn, user["id"])
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/plans")
def get_plans(user=Depends(current_user)):
    conn = db.connect()
    plans = db.load_user_plans(conn, user["id"])
    conn.close()
    return plans


class PlanChange(BaseModel):
    # Size limits, so nobody can store huge texts in someone else's database
    source: str = Field(max_length=100)
    title_key: str = Field(max_length=500)
    status: Literal["want", "going"] | None  # None removes the plan
    category: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=500)
    start_date: str | None = Field(default=None, max_length=10)
    link: str | None = Field(default=None, max_length=2000)


@app.put("/api/plans")
def change_plan(change: PlanChange, user=Depends(current_user)):
    conn = db.connect()
    if change.status and db.count_user_plans(conn, user["id"]) >= MAX_PLANS:
        existing = {(p["source"], p["title_key"]) for p in db.load_user_plans(conn, user["id"])}
        if (change.source, change.title_key) not in existing:
            conn.close()
            raise HTTPException(status_code=400, detail=f"You can save up to {MAX_PLANS} plans. Remove some first.")
    db.set_user_plan(conn, user["id"], change.model_dump(exclude={"status"}), change.status)
    conn.commit()
    conn.close()
    return {"ok": True}