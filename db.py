import os
import sqlite3

import clock

from difflib import SequenceMatcher

DB_PATH = "promos.db"
tables_ready = False  # the CREATE TABLE checks only need to run once each time the server starts


def open_database():
    """Online the data lives in Turso; on your computer it's the promos.db file."""
    url = os.getenv("TURSO_DATABASE_URL", "").strip()
    if url:
        import turso_serverless  # only needed online
        token = os.getenv("TURSO_AUTH_TOKEN", "").strip()  # ignore stray spaces or line breaks from pasting
        conn = turso_serverless.connect(url, auth_token=token)
        conn.row_factory = turso_serverless.Row  # lets us read rows like dictionaries
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read rows like dictionaries
    return conn


def connect():
    global tables_ready
    conn = open_database()
    if tables_ready:
        return conn
    conn.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            title_key TEXT NOT NULL,
            details TEXT,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            channel TEXT,
            link TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            UNIQUE(source, title_key)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS refreshes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refreshed_at TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            source TEXT NOT NULL,
            title_key TEXT NOT NULL,
            status TEXT NOT NULL,
            category TEXT,
            title TEXT,
            start_date TEXT,
            link TEXT,
            PRIMARY KEY (source, title_key)
        )
    """)
    # Sign in with Google: one row per person, and each person's own Want / Going plans
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_plans (
            user_id TEXT NOT NULL,
            source TEXT NOT NULL,
            title_key TEXT NOT NULL,
            status TEXT NOT NULL,
            category TEXT,
            title TEXT,
            start_date TEXT,
            link TEXT,
            PRIMARY KEY (user_id, source, title_key)
        )
    """)
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(promos)")]
    if "topic" not in columns:
        conn.execute("ALTER TABLE promos ADD COLUMN topic TEXT")  # upgrade databases made before topics existed
    tables_ready = True
    return conn


def make_key(title):
    # "Good Reads,  Great Value!" and "good reads, great value!" count as the same promo
    return " ".join(title.lower().split())


def start_refresh(conn, category):
    now = clock.now().isoformat(timespec="seconds")
    conn.execute("INSERT INTO refreshes (refreshed_at, category) VALUES (?, ?)", (now, category))
    conn.commit()
    return now

def similar(a, b):
    shorter = min(a, b, key=len)
    contains = len(shorter) >= 12 and (a in b or b in a)
    return a == b or contains or SequenceMatcher(None, a, b).ratio() >= 0.85


def find_existing(conn, row):
    """Return (source, title_key) of a row that's really the same item, or this row's own key."""
    key = make_key(row["title"])
    if row["category"] != "bookstore_promo":
        # Events: the same link means the same event, whichever feed it came from
        if row.get("link"):
            hit = conn.execute(
                "SELECT source, title_key FROM promos WHERE category = ? AND link = ?",
                (row["category"], row["link"]),
            ).fetchone()
            if hit:
                return hit["source"], hit["title_key"]
        # ...and so do overlapping dates with a near-identical title, even from another site.
        # (Sites disagree by a day sometimes: one lists 19-22 Nov, another 20-22 Nov.)
        # Oldest first, so the copy saved first always wins.
        if row["start_date"]:
            for existing in conn.execute(
                """SELECT source, title_key FROM promos
                   WHERE category = ? AND start_date <= ? AND COALESCE(end_date, start_date) >= ?
                   ORDER BY id""",
                (row["category"], row["end_date"] or row["start_date"], row["start_date"]),
            ):
                if similar(key, existing["title_key"]):
                    return existing["source"], existing["title_key"]
        return row["source"], key

    # Promos: the LLM words titles slightly differently between runs, so match close titles
    for existing in conn.execute("SELECT title_key FROM promos WHERE source = ?", (row["source"],)):
        if similar(key, existing["title_key"]):
            return row["source"], existing["title_key"]
    return row["source"], key


def save_promo(conn, row, run_time):
    source, title_key = find_existing(conn, row)
    if source != row["source"]:
        # already saved from another source: keep its details, just note it's still listed
        conn.execute(
            "UPDATE promos SET last_seen = ? WHERE source = ? AND title_key = ?",
            (run_time, source, title_key),
        )
        return
    conn.execute("""
        INSERT INTO promos (source, category, title, title_key, details, start_date, end_date,
                            location, channel, link, topic, first_seen, last_seen)
        VALUES (:source, :category, :title, :title_key, :details, :start_date, :end_date,
                :location, :channel, :link, :topic, :run_time, :run_time)
        ON CONFLICT(source, title_key) DO UPDATE SET
            title = excluded.title,
            details = COALESCE(excluded.details, promos.details),
            start_date = COALESCE(excluded.start_date, promos.start_date),
            end_date = COALESCE(excluded.end_date, promos.end_date),
            location = COALESCE(excluded.location, promos.location),
            channel = COALESCE(excluded.channel, promos.channel),
            link = COALESCE(excluded.link, promos.link),
            topic = COALESCE(excluded.topic, promos.topic),
            last_seen = excluded.last_seen
    """, {**row, "source": source, "title_key": title_key, "run_time": run_time})


def load_promos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM promos").fetchall()]


def refresh_info(conn, category):
    row = conn.execute(
        "SELECT COUNT(*) AS count, MAX(refreshed_at) AS latest FROM refreshes WHERE category = ?",
        (category,),
    ).fetchone()
    return dict(row)

def load_plans(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM plans ORDER BY start_date")]


def set_plan(conn, item, status):
    """status is 'want', 'going', or None to remove the plan."""
    if status is None:
        conn.execute("DELETE FROM plans WHERE source = ? AND title_key = ?", (item["source"], item["title_key"]))
        return
    conn.execute("""
        INSERT INTO plans (source, title_key, status, category, title, start_date, link)
        VALUES (:source, :title_key, :status, :category, :title, :start_date, :link)
        ON CONFLICT(source, title_key) DO UPDATE SET status = excluded.status
    """, {**item, "status": status})
    

# ---------- Accounts (Sign in with Google) ----------
# The old plans table above is still used by the Streamlit app (app.py).

def get_user(conn, user_id):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def save_user(conn, user_id, email, name):
    """Adds a new person, or updates their email and name. Returns True if they're new."""
    is_new = get_user(conn, user_id) is None
    conn.execute("""
        INSERT INTO users (id, email, name, created_at) VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET email = excluded.email, name = excluded.name
    """, (user_id, email, name, clock.now().isoformat(timespec="seconds")))
    return is_new


def delete_user(conn, user_id):
    """Removes a person and all their plans for good."""
    conn.execute("DELETE FROM user_plans WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def copy_old_plans(conn, user_id):
    """Gives the plans made before accounts existed to the site owner."""
    conn.execute("""
        INSERT OR IGNORE INTO user_plans (user_id, source, title_key, status, category, title, start_date, link)
        SELECT ?, source, title_key, status, category, title, start_date, link FROM plans
    """, (user_id,))


def load_user_plans(conn, user_id):
    rows = conn.execute(
        "SELECT source, title_key, status, category, title, start_date, link FROM user_plans "
        "WHERE user_id = ? ORDER BY start_date",
        (user_id,),
    )
    return [dict(r) for r in rows]


def set_user_plan(conn, user_id, item, status):
    """status is 'want', 'going', or None to remove the plan."""
    if status is None:
        conn.execute(
            "DELETE FROM user_plans WHERE user_id = ? AND source = ? AND title_key = ?",
            (user_id, item["source"], item["title_key"]),
        )
        return
    conn.execute("""
        INSERT INTO user_plans (user_id, source, title_key, status, category, title, start_date, link)
        VALUES (:user_id, :source, :title_key, :status, :category, :title, :start_date, :link)
        ON CONFLICT(user_id, source, title_key) DO UPDATE SET status = excluded.status
    """, {**item, "user_id": user_id, "status": status})

def count_user_plans(conn, user_id):
    return conn.execute("SELECT COUNT(*) AS n FROM user_plans WHERE user_id = ?", (user_id,)).fetchone()["n"]