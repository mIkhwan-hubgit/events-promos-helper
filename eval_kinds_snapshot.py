import json
from pathlib import Path

from fetcher import fetch_cloudjoi_events

FOLDER = Path("eval/kinds")
EVENTS_FILE = FOLDER / "cloudjoi_events.json"
LABELS_FILE = FOLDER / "expected_kinds.json"

if EVENTS_FILE.exists():
    print(f"{EVENTS_FILE} already exists - not overwriting the frozen snapshot.")
else:
    FOLDER.mkdir(parents=True, exist_ok=True)
    events = fetch_cloudjoi_events("https://www.cloudjoi.com/")
    frozen = [{"title": e["title"], "description": e["description"], "link": e["link"]} for e in events]
    EVENTS_FILE.write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")

    labels = [{"title": e["title"], "info": e["description"], "link": e["link"], "kind": None} for e in frozen]
    LABELS_FILE.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(frozen)} events. Now label every one in {LABELS_FILE}.")