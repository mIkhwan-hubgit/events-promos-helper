"""Refreshes every tab, one after another.

GitHub Actions runs this every morning (see .github/workflows/daily-refresh.yml).
You can also run it yourself with:  python refresh_all.py

With --skip-if-done-today, tabs that were already refreshed today (Malaysia time) are left alone.
GitHub's own backup schedule uses this, so it only fills in if the 7 a.m. run didn't happen.
"""
import sys

from dotenv import load_dotenv

load_dotenv()

import clock  # noqa: E402 (needs the settings loaded first)
import db  # noqa: E402
from pipeline import CATEGORIES, refresh  # noqa: E402

skip_if_done = "--skip-if-done-today" in sys.argv
today = clock.today().isoformat()

for category, label in CATEGORIES.items():
    print(f"\n=== {label} ===", flush=True)
    if skip_if_done:
        conn = db.connect()
        latest = db.refresh_info(conn, category)["latest"]
        conn.close()
        if latest and clock.parse(latest).date().isoformat() == today:
            print("  already refreshed today, skipping", flush=True)
            continue
    problems = refresh(category)
    for problem in problems:
        print(f"  ! {problem}", flush=True)
    print("  finished" + (f" with {len(problems)} problem(s)" if problems else ""), flush=True)