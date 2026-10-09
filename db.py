import sqlite3
from datetime import datetime

DB_PATH = "promos.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read rows like dictionaries
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
            refreshed_at TEXT NOT NULL
        )
    """)
    return conn


def make_key(title):
    # "Good Reads,  Great Value!" and "good reads, great value!" count as the same promo
    return " ".join(title.lower().split())


def start_refresh(conn):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("INSERT INTO refreshes (refreshed_at) VALUES (?)", (now,))
    conn.commit()
    return now


def save_promo(conn, row, run_time):
    conn.execute("""
        INSERT INTO promos (source, category, title, title_key, details, start_date, end_date,
                            location, channel, link, first_seen, last_seen)
        VALUES (:source, :category, :title, :title_key, :details, :start_date, :end_date,
                :location, :channel, :link, :run_time, :run_time)
        ON CONFLICT(source, title_key) DO UPDATE SET
            title = excluded.title,
            details = excluded.details,
            start_date = excluded.start_date,
            end_date = excluded.end_date,
            location = excluded.location,
            channel = excluded.channel,
            link = excluded.link,
            last_seen = excluded.last_seen
    """, {**row, "title_key": make_key(row["title"]), "run_time": run_time})


def load_promos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM promos").fetchall()]


def refresh_info(conn):
    row = conn.execute(
        "SELECT COUNT(*) AS count, MAX(refreshed_at) AS latest FROM refreshes"
    ).fetchone()
    return dict(row)