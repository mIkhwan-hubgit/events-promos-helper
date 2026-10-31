import sqlite3

import clock

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
            refreshed_at TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(promos)")]
    if "topic" not in columns:
        conn.execute("ALTER TABLE promos ADD COLUMN topic TEXT")  # upgrade databases made before topics existed
    return conn


def make_key(title):
    # "Good Reads,  Great Value!" and "good reads, great value!" count as the same promo
    return " ".join(title.lower().split())


def start_refresh(conn, category):
    now = clock.now().isoformat(timespec="seconds")
    conn.execute("INSERT INTO refreshes (refreshed_at, category) VALUES (?, ?)", (now, category))
    conn.commit()
    return now


def save_promo(conn, row, run_time):
    conn.execute("""
        INSERT INTO promos (source, category, title, title_key, details, start_date, end_date,
                            location, channel, link, topic, first_seen, last_seen)
        VALUES (:source, :category, :title, :title_key, :details, :start_date, :end_date,
                :location, :channel, :link, :topic, :run_time, :run_time)
        ON CONFLICT(source, title_key) DO UPDATE SET
            title = excluded.title,
            details = excluded.details,
            start_date = excluded.start_date,
            end_date = excluded.end_date,
            location = excluded.location,
            channel = excluded.channel,
            link = excluded.link,
            topic = excluded.topic,
            last_seen = excluded.last_seen
    """, {**row, "title_key": make_key(row["title"]), "run_time": run_time})


def load_promos(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM promos").fetchall()]


def refresh_info(conn, category):
    row = conn.execute(
        "SELECT COUNT(*) AS count, MAX(refreshed_at) AS latest FROM refreshes WHERE category = ?",
        (category,),
    ).fetchone()
    return dict(row)