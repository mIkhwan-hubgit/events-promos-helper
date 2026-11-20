"""One-off: copy everything from promos.db (on your computer) into the online Turso database.

Run it once with:  python copy_to_turso.py
It's safe to run again: rows that are already there are simply replaced.
"""
import getpass
import os
import sqlite3

import db

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
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
    for row in rows:
        remote.execute(sql, [row[c] for c in columns])
    remote.commit()
    print(f"{table}: copied {len(rows)} rows")

remote.close()
local.close()
print("Done!")