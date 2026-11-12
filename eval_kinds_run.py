import html
import json
import time
from pathlib import Path

from llm import classify_events

FOLDER = Path("eval/kinds")
events = json.loads((FOLDER / "cloudjoi_events.json").read_text(encoding="utf-8"))
labels = json.loads((FOLDER / "expected_kinds.json").read_text(encoding="utf-8"))

unlabelled = [l["title"] for l in labels if l["kind"] not in ("orchestra", "workshop", "none")]
if unlabelled:
    raise SystemExit(f"Label every event first. Missing or misspelled ({len(unlabelled)}): {unlabelled[:5]}")


def with_patience(job, attempts=5, wait=60):
    for attempt in range(attempts):
        try:
            return job()
        except RuntimeError as e:
            if attempt == attempts - 1:
                raise
            print(f"{e} Waiting {wait} seconds, then trying again ({attempt + 1}/{attempts - 1})...")
            time.sleep(wait)


def pct(part, whole):
    return f"{part / whole:.0%}" if whole else "n/a"


expected = {l["title"]: l["kind"] for l in labels}
model_input = [
    {**e, "description": e["description"] + (f" About: {html.unescape(e['page_summary'])}" if e.get("page_summary") else "")}
    for e in events
]
picks = with_patience(lambda: classify_events(model_input, "CloudJoi (eval)", allow_fallback=False))
predicted = {title: "none" for title in expected}
for event in picks:
    predicted[event["title"]] = event["category"]

for title, want in expected.items():
    got = predicted[title]
    if got != want or want != "none":  # show every mistake, plus every correct orchestra/workshop pick
        mark = "OK   " if got == want else "WRONG"
        print(f"  {mark}: {title}  (model: {got}, expected: {want})")

print("\n===== Summary =====")
for kind in ("orchestra", "workshop"):
    hits = sum(1 for t in expected if expected[t] == kind and predicted[t] == kind)
    should = sum(1 for t in expected if expected[t] == kind)
    picked = sum(1 for t in expected if predicted[t] == kind)
    print(f"{kind:9}  recall {hits}/{should} = {pct(hits, should)}   precision {hits}/{picked} = {pct(hits, picked)}")
right = sum(1 for t in expected if predicted[t] == expected[t])
print(f"Overall: {right}/{len(expected)} = {pct(right, len(expected))} of events sorted correctly (including 'none')")