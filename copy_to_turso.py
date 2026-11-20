"""One-off: copy everything from promos.db (on your computer) into the online Turso database.

Run it once with:  python copy_to_turso.py
It's safe to run again: rows that are already there are simply replaced.
"""
import getpass
import os
import sqlite3
import time

import db

CHUNK = 25  # rows sent per request: fewer trips over the internet

url = input("Turso database URL (starts with libsql://): ").strip()
token = getpass.getpass("Turso token (it stays invisible while you paste, that's normal): ").strip()
os.environ["TURSO_DATABASE_URL"] = url
os.environ["TURSO_AUTH_TOKEN"] = token

local = sqlite3.connect(db.DB_PATH)
local.row_factory = sqlite3.Row
remote = db.connect()  # this also creates the tables in Turso

for table in ["promos", "refreshes", "plans"]:
    rows = [dict(r) for r in local.execute(f"SELECT * FROM {table}")]
    if not rows:
        print(f"{table}: nothing to copy")
        continue
    columns = list(rows[0])
    one_row = "(" + ", ".join("?" for _ in columns) + ")"
    for start in range(0, len(rows), CHUNK):
        chunk = rows[start : start + CHUNK]
        sql = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES {', '.join(one_row for _ in chunk)}"
        values = [row[c] for row in chunk for c in columns]
        for attempt in range(3):  # the internet sometimes hiccups: try each chunk up to 3 times
            try:
                remote.execute(sql, values)
                remote.commit()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"  {table}: connection problem ({e.__class__.__name__}), trying again in 5 seconds...")
                remote.close()
                time.sleep(5)
                remote = db.open_database()
        print(f"{table}: copied {min(start + CHUNK, len(rows))} of {len(rows)} rows")

remote.close()
local.close()
print("Done!")