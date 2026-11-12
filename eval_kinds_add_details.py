import json
from pathlib import Path

from fetcher import DETAIL_CATEGORIES, cloudjoi_page_summary

FILE = Path("eval/kinds/cloudjoi_events.json")
events = json.loads(FILE.read_text(encoding="utf-8"))

found = 0
for event in events:
    if "page_summary" in event:
        continue  # already added; never re-download into a frozen snapshot
    categories = set(event["description"].split(".")[0].removeprefix("Category: ").split(", "))
    if categories & DETAIL_CATEGORIES:  # same rule as the app
        event["page_summary"] = cloudjoi_page_summary(event["link"])
        found += bool(event["page_summary"])
    else:
        event["page_summary"] = ""

FILE.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Added page summaries: {found} found.")
nine = next((e for e in events if e["title"] == "The 9th"), None)
if nine:
    print("The 9th now says:", nine["page_summary"][:300])