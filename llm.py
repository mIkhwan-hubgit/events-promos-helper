import hashlib
import json
import os
import time
import clock
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types

from schema import Promo, TechPick

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL")
CACHE_DIR = Path(".cache")

PROMPT = """You extract bookstore promotions and events from web page text.
Today's date is {today}.

Rules:
- Only include real promotions, sales, bookfairs or events. Ignore menus, footers and navigation links.
- Ignore discounts on individual products (e.g. one book at 60% off). Only include store-wide promotions, sales campaigns, promo codes, bookfairs and events.
- Ignore permanent store policies such as standard shipping fees, delivery terms or minimum-spend shipping rules.
- Include every promotion in the text. Do not skip any.
- Write dates as YYYY-MM-DD. If only a month is given (e.g. "Sept 2026"), use the first and last day of that month.
- If a post says something like "this October" without exact dates, use the whole of that month, in the year the post was published.
- If no start date is stated but the post has a published date, use the published date as start_date.
- Pages may mix English and Malay (e.g. Julai = July, Ogos = August, Okt = October).
- details should describe the offer itself (e.g. "15% off featured finance titles"). Do not repeat the location there. If the text doesn't describe the offer beyond its title, use null. Never copy the title into details.
- channel: where the offer can be used. "in_store" = at physical stores or a physical event (a bookfair, a named store or mall). "online" = online orders (e.g. "valid for webstore orders", a promo code entered at checkout, e-gift cards, items you add to cart). "both" = clearly both. Use null if the text and images don't make it clear. Do not guess, and never put a place name here; that belongs in location.
- If the text gives a link for a promotion, put it in link.
- Some posts come with a banner image, labelled with the post's title. Read the text in each image too. If an image shows an offer (such as a discount), include it in that promotion, even when the post text doesn't mention it.
- Only include promotions and events in Malaysia or available to Malaysian customers. Skip ones in other countries.
- If something is not stated, use null. Never make up details.
- If the same offer appears more than once (e.g. the same promo code in two places), list it only once.

Page text from {source}:
{text}
"""


def call_gemini(contents, source, schema=list[Promo], allow_fallback=True, retries=3):
    models = [MODEL] + ([FALLBACK_MODEL] if FALLBACK_MODEL and allow_fallback else [])

    for model in models:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                        "temperature": 0,
                    },
                )
                if response.parsed is None:
                    print(f"{source}: {model} replied in the wrong format, trying again...")
                    continue  # counts as a failed attempt
                print(f"{source}: {model} answered with {len(response.parsed)} promos")
                return response.parsed, model
            except errors.ServerError:
                if attempt < retries - 1:
                    wait = 5 * (attempt + 1)
                    print(f"{source}: {model} is busy, retrying in {wait} seconds...")
                    time.sleep(wait)
            except errors.ClientError as e:
                if e.code == 429:
                    print(f"{source}: {model} has used up its free quota, trying the next model...")
                    break  # no point retrying this model today
                raise  # any other client error (e.g. bad key) should stop immediately
        print(f"{source}: moving on from {model}...")

    raise RuntimeError("Gemini is unavailable right now (busy, or the daily free limit is used up). Try again later.")


def extract_promos(source, text, images=None, allow_fallback=True):
    images = images or []
    prompt = PROMPT.format(today=clock.today().isoformat(), source=source, text=text)

    # The fingerprint covers the prompt AND every image, so a changed banner means a fresh answer
    hasher = hashlib.sha256(prompt.encode("utf-8"))
    for img in images:
        hasher.update(img["data"])
    cache_file = CACHE_DIR / f"{hasher.hexdigest()}.json"
    if cache_file.exists():
        print(f"{source}: page unchanged, using cached result")
        saved = json.loads(cache_file.read_text(encoding="utf-8"))
        return [Promo(**item) for item in saved]

    contents = [prompt]
    for img in images:
        contents.append(f"Banner image for the post titled: {img['label']}")
        contents.append(types.Part.from_bytes(data=img["data"], mime_type=img["mime"]))

    promos, model_used = call_gemini(contents, source, allow_fallback=allow_fallback)
    if not promos:
        return promos  # don't cache empty results, they're probably a mistake
    if model_used != MODEL:
          return promos  # don't cache fallback answers: next time, try the main model again
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(
        json.dumps([p.model_dump(mode="json") for p in promos], ensure_ascii=False),
        encoding="utf-8",
    )
    return promos

TECH_PROMPT = """Below is a numbered list of events in and around Kuala Lumpur.
Return the numbers of the events that are tech events.

Tech events are mainly about software, AI, data, cybersecurity, cloud, hardware or IoT,
digital product design, developer communities, hackathons, or technology-focused startups.
Not tech events: fitness, food and drink, art and crafts, music and dance, general social
mixers, and business events where technology is not the main focus.

For each tech event, also give its main topic. Only use the Startup topic for events mainly about
building technology products or tech companies. Choosing a topic does not change the rule above:
founder, business and funding events where technology is not the main focus are still not tech events.

{items}
"""


def pick_tech_events(events, source, allow_fallback=True):
    if not events:
        return []
    items = "\n\n".join(f"{i}. {e['title']}\n{e['description'][:600]}" for i, e in enumerate(events))
    prompt = TECH_PROMPT.format(items=items)

    cache_file = CACHE_DIR / f"tech_{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}.json"
    if cache_file.exists():
        print(f"{source}: events unchanged, using cached result")
        picks = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        result, model_used = call_gemini(prompt, source, schema=list[TechPick], allow_fallback=allow_fallback)
        picks = [p.model_dump(mode="json") for p in result]
        if model_used == MODEL:  # same rule as before: don't cache fallback answers
            CACHE_DIR.mkdir(exist_ok=True)
            cache_file.write_text(json.dumps(picks), encoding="utf-8")

    chosen, seen = [], set()
    for pick in picks:
        i = pick["index"]
        if 0 <= i < len(events) and i not in seen:
            seen.add(i)
            chosen.append({**events[i], "topic": pick["topic"]})
    return chosen
