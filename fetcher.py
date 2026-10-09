import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import feedparser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}


def fetch_text(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()  # stop with an error if status isn't 200
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text(separator="\n", strip=True)

def fetch_feed_text(url, max_age_days=45):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    parts = []
    for entry in feed.entries:
        when = entry.get("published_parsed") or entry.get("updated_parsed")
        published = datetime(*when[:6], tzinfo=timezone.utc) if when else None
        if published and published < cutoff:
            continue  # skip old posts

        if "content" in entry:
            html = entry.content[0].value
        else:
            html = entry.get("summary", "")
        body = BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)

        date_text = published.date().isoformat() if published else "unknown"
        parts.append(f"Title: {entry.title}\nPublished: {date_text}\nLink: {entry.link}\n{body}")

    return "\n\n---\n\n".join(parts)