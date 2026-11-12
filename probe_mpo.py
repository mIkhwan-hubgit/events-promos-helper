import feedparser
import requests
from bs4 import BeautifulSoup

from fetcher import HEADERS

print("===== myticket.asia feed =====")
try:
    response = requests.get("https://myticket.asia/feed/", headers=HEADERS, timeout=20)
    print("Status:", response.status_code)
    feed = feedparser.parse(response.content)
    print("Entries:", len(feed.entries))
    for entry in feed.entries[:8]:
        print(" -", entry.get("published", "?")[:16], "|", entry.get("title", "(no title)"))
except Exception as e:
    print("Failed:", e)

print("\n===== One MPO concert page =====")
try:
    response = requests.get("https://myticket.asia/?p=4646", headers=HEADERS, timeout=20)
    print("Status:", response.status_code, "| final URL:", response.url)
    soup = BeautifulSoup(response.text, "html.parser")
    blocks = soup.find_all("script", type="application/ld+json")
    print("Structured data blocks:", len(blocks))
    for block in blocks[:2]:
        print((block.string or "(empty)")[:600])
except Exception as e:
    print("Failed:", e)