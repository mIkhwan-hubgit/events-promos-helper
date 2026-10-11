import json
from pathlib import Path

from fetcher import fetch_text, fetch_feed_text
from llm import extract_promos
from sources import SOURCES

FETCHERS = {"html": fetch_text, "feed": fetch_feed_text}
EVAL_DIR = Path("eval")
(EVAL_DIR / "pages").mkdir(parents=True, exist_ok=True)
expected_file = EVAL_DIR / "expected.json"

draft = {}
for source in SOURCES:
    text = FETCHERS[source["type"]](source["url"])
    (EVAL_DIR / "pages" / f"{source['name']}.txt").write_text(text, encoding="utf-8")
    promos = extract_promos(source["name"], text)
    draft[source["name"]] = [
        {"title": p.title, "start_date": p.start_date, "end_date": p.end_date, "must_mention": []}
        for p in promos
    ]
    print(f"Saved {source['name']}")

if expected_file.exists():
    print("expected.json already exists, so it was NOT overwritten (your hand-checked answers are safe).")
else:
    expected_file.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Created a DRAFT eval/expected.json. Now check it by hand!")