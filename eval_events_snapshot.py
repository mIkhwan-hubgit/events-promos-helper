import json
from pathlib import Path

from fetcher import fetch_ical_bytes, parse_ical_events
from sources import SOURCES

EVENTS_DIR = Path("eval") / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
snapshot = EVENTS_DIR / "luma_kl.ics"
expected_file = EVENTS_DIR / "expected_tech.json"

if snapshot.exists():
    print("Snapshot already exists, not overwriting (delete it on purpose to re-snapshot).")
else:
    source = next(s for s in SOURCES if s.get("tech_filter"))
    snapshot.write_bytes(fetch_ical_bytes(source["url"]))
    print(f"Saved {snapshot}")

if expected_file.exists():
    print("expected_tech.json already exists, so it was NOT overwritten.")
else:
    events = parse_ical_events(snapshot.read_bytes())
    draft = {e["title"]: None for e in events}
    expected_file.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created a blank answer sheet with {len(draft)} events. Mark each one true (tech) or false (not tech).")