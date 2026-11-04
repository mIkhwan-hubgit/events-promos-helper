import json
from pathlib import Path

from fetcher import parse_ical_events
from llm import pick_tech_events

EVENTS_DIR = Path("eval") / "events"
expected = json.loads((EVENTS_DIR / "expected_tech.json").read_text(encoding="utf-8"))
if any(v is None for v in expected.values()):
    raise SystemExit("Some events in expected_tech.json are still null. Mark each one true or false first.")


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


events = parse_ical_events((EVENTS_DIR / "luma_kl.ics").read_bytes())
picked = {e["title"] for e in pick_tech_events(events, "Luma KL (eval)", allow_fallback=False)}
should = {title for title, is_tech in expected.items() if is_tech}

for title, is_tech in expected.items():
    got = title in picked
    if got == is_tech:
        label = "OK     "
    else:
        label = "MISSED " if is_tech else "EXTRA  "
    print(f"  {label}: {title}  (expected {'tech' if is_tech else 'not tech'})")

found = len(picked & should)
print("\n===== Summary =====")
print(f"Recall    (tech events found / all tech events): {found}/{len(should)} = {pct(found, len(should))}")
print(f"Precision (real tech / everything picked):      {found}/{len(picked)} = {pct(found, len(picked))}")