import json
from difflib import SequenceMatcher
from pathlib import Path
import time

from llm import extract_promos
from llm import DailyQuotaUsed

EVAL_DIR = Path("eval")
MATCH_THRESHOLD = 0.7
expected_all = json.loads((EVAL_DIR / "expected.json").read_text(encoding="utf-8"))


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()  # 0 = different, 1 = identical


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


def match(expected, predicted):
    # Score every possible pair, then lock in the best pairs first
    pairs = sorted(
        ((similar(p.title, exp["title"]), i, j)
         for i, exp in enumerate(expected)
         for j, p in enumerate(predicted)),
        reverse=True,
    )
    matches, used = {}, set()
    for score, i, j in pairs:
        if score < MATCH_THRESHOLD:
            break
        if i in matches or j in used:
            continue
        matches[i] = j
        used.add(j)
    return matches, used

def load_images(source):
    img_dir = EVAL_DIR / "pages" / f"{source}_images"
    manifest_file = img_dir / "manifest.json"
    if not manifest_file.exists():
        return []
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    return [
        {"label": m["label"], "mime": m["mime"], "data": (img_dir / m["file"]).read_bytes()}
        for m in manifest
    ]

def with_patience(job, attempts=5, wait=60):
    for attempt in range(attempts):
        try:
            return job()
        except DailyQuotaUsed:
            raise  # waiting won't help; stop straight away
        except RuntimeError as e:
            if attempt == attempts - 1:
                raise
            print(f"{e} Waiting {wait} seconds, then trying again ({attempt + 1}/{attempts - 1})...")
            time.sleep(wait)

totals = {"expected": 0, "predicted": 0, "found": 0, "dates_ok": 0, "mentions_ok": 0, "mentions_total": 0, "channel_ok": 0, "channel_total": 0}

for source, expected in expected_all.items():
    text = (EVAL_DIR / "pages" / f"{source}.txt").read_text(encoding="utf-8")
    predicted = with_patience(lambda: extract_promos(source, text, load_images(source), allow_fallback=False))
    matches, used = match(expected, predicted)
    print(f"\n===== {source} =====")

    for i, exp in enumerate(expected):
        if i not in matches:
            print(f"  MISSED : {exp['title']}")
            continue
        got = predicted[matches[i]]
        totals["found"] += 1

        problems = []
        dates_ok = got.start_date == exp["start_date"] and got.end_date == exp["end_date"]
        totals["dates_ok"] += dates_ok
        if not dates_ok:
            problems.append(f"dates {got.start_date} to {got.end_date}, expected {exp['start_date']} to {exp['end_date']}")

        searchable = f"{got.title} {got.details or ''}".lower()  # title counts too: details mustn't repeat it
        for word in exp.get("must_mention", []):
            totals["mentions_total"] += 1
            if word.lower() in searchable:
                totals["mentions_ok"] += 1
            else:
                problems.append(f"missing '{word}'")

        if "channel" in exp:
            totals["channel_total"] += 1
            if got.channel == exp["channel"]:
                totals["channel_ok"] += 1
            else:
                problems.append(f"channel {got.channel}, expected {exp['channel']}")

        label = "PARTIAL" if problems else "OK     "
        note = f"  ({'; '.join(problems)})" if problems else ""
        print(f"  {label}: {exp['title']}{note}")

    for j, p in enumerate(predicted):
        if j not in used:
            print(f"  EXTRA  : {p.title}")

    totals["expected"] += len(expected)
    totals["predicted"] += len(predicted)

print("\n===== Summary =====")
print(f"Recall    (found / should find):   {totals['found']}/{totals['expected']} = {pct(totals['found'], totals['expected'])}")
print(f"Precision (real / returned):       {totals['found']}/{totals['predicted']} = {pct(totals['found'], totals['predicted'])}")
print(f"Dates exactly right:               {totals['dates_ok']}/{totals['found']} = {pct(totals['dates_ok'], totals['found'])}")
print(f"Key details mentioned:             {totals['mentions_ok']}/{totals['mentions_total']} = {pct(totals['mentions_ok'], totals['mentions_total'])}")
print(f"Channel right:                     {totals['channel_ok']}/{totals['channel_total']} = {pct(totals['channel_ok'], totals['channel_total'])}")