from fetcher import fetch_text
from llm import extract_promos

SOURCE = "POPULAR"
URL = "https://www.popular.com.my/ongoing-promotions/"

text = fetch_text(URL)
promos = extract_promos(SOURCE, text)

print(f"Found {len(promos)} promos:\n")
for p in promos:
    print(f"- {p.title}")
    print(f"    {p.start_date} to {p.end_date} | {p.location} | {p.channel}")
    if p.details:
        print(f"    {p.details}")