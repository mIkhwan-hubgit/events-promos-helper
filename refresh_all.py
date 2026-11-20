"""Refreshes every tab, one after another.

GitHub Actions runs this every morning (see .github/workflows/daily-refresh.yml).
You can also run it yourself with:  python refresh_all.py
"""
from dotenv import load_dotenv

load_dotenv()

from pipeline import CATEGORIES, refresh  # noqa: E402 (needs the settings loaded first)

for category, label in CATEGORIES.items():
    print(f"\n=== {label} ===", flush=True)
    problems = refresh(category)
    for problem in problems:
        print(f"  ! {problem}", flush=True)
    print("  finished" + (f" with {len(problems)} problem(s)" if problems else ""), flush=True)