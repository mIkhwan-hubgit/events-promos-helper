import time
from google.genai import errors
import os
from datetime import date
from dotenv import load_dotenv
from google import genai
from schema import Promo

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")

PROMPT = """You extract bookstore promotions and events from web page text.
Today's date is {today}.

Rules:
- Only include real promotions, sales, bookfairs or events. Ignore menus, footers and navigation links.
- Write dates as YYYY-MM-DD. If only a month is given (e.g. "Sept 2026"), use the first and last day of that month.
- Pages may mix English and Malay (e.g. Julai = July, Ogos = August, Okt = October).
- channel must be "in_store", "online" or "both".
- If something is not stated, use null or -. Never make up details.

Page text from {source}:
{text}
"""


def extract_promos(source, text, retries=3):
       for attempt in range(retries):
           try:
               response = client.models.generate_content(
                   model=MODEL,
                   contents=PROMPT.format(today=date.today().isoformat(), source=source, text=text),
                   config={
                       "response_mime_type": "application/json",
                       "response_schema": list[Promo],
                   },
               )
               return response.parsed or []
           except errors.ServerError:
               if attempt == retries - 1:
                   raise  # tried enough times, give up and show the error
               wait = 5 * (attempt + 1)
               print(f"Gemini is busy, retrying in {wait} seconds...")
               time.sleep(wait)