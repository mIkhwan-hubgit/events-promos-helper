import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from schema import Promo

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
- channel must be "in_store", "online" or "both".
- If the text gives a link for a promotion, put it in link.
- If something is not stated, use null. Never make up details.

Page text from {source}:
{text}
"""


def call_gemini(prompt, retries=3):
    models = [MODEL] + ([FALLBACK_MODEL] if FALLBACK_MODEL else [])

    for model in models:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": list[Promo],
                        "temperature": 0,
                    },
                )
                return response.parsed or []
            except errors.ServerError:
                if attempt < retries - 1:
                    wait = 5 * (attempt + 1)
                    print(f"{model} is busy, retrying in {wait} seconds...")
                    time.sleep(wait)
            except errors.ClientError as e:
                if e.code == 429:
                    print(f"{model} has used up its free quota, trying the next model...")
                    break  # no point retrying this model today
                raise  # any other client error (e.g. bad key) should stop immediately
        print(f"Moving on from {model}...")

    raise RuntimeError("Gemini is unavailable right now (busy, or the daily free limit is used up). Try again later.")


def extract_promos(source, text):
    prompt = PROMPT.format(today=date.today().isoformat(), source=source, text=text)

    # Same prompt as before? Reuse the saved answer instead of calling Gemini again.
    key = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        print(f"{source}: page unchanged, using cached result")
        saved = json.loads(cache_file.read_text(encoding="utf-8"))
        return [Promo(**item) for item in saved]

    promos = call_gemini(prompt)
    if not promos:
        return promos  # don't cache empty results, they're probably a mistake
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(
        json.dumps([p.model_dump() for p in promos], ensure_ascii=False),
        encoding="utf-8",
    )
    return promos
