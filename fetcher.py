import hashlib
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from icalendar import Calendar

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}
MYT = timezone(timedelta(hours=8))  # Malaysia time, UTC+8
BANNER_DIR = Path(".cache") / "banners"
OFFER_HINT = re.compile(r"\d+\s*%|RM\s?\d+|\bfree\b", re.IGNORECASE)  # e.g. "15%", "RM10", "free"


class RateLimited(Exception):
    """The website told us to slow down (HTTP 429)."""


def polite_get(url, delay=2.0):
    time.sleep(delay)  # small pause before every request
    response = requests.get(url, headers=HEADERS, timeout=20)
    if response.status_code == 429:
        raise RateLimited(url)  # don't wait around; let the caller decide what to do
    response.raise_for_status()
    return response


def fetch_text(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()  # stop with an error if status isn't 200
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text(separator="\n", strip=True), []  # no images yet for plain pages


def find_banner_image(page_url):
    response = polite_get(page_url)
    soup = BeautifulSoup(response.text, "html.parser")
    tag = soup.find("meta", property="og:image:secure_url") or soup.find("meta", property="og:image")
    return tag["content"] if tag and tag.get("content") else None


def download_image(url):
    response = polite_get(url)
    mime = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
    return response.content, mime


def wants_banner(body):
    # Only look at the banner when the text doesn't already mention an offer
    return not OFFER_HINT.search(body)


def get_banner(post_url, allow_download=True):
    """Return (data, mime) for a post's banner, using the saved copy if we have one."""
    key = hashlib.sha256(post_url.encode("utf-8")).hexdigest()
    data_file = BANNER_DIR / f"{key}.img"
    meta_file = BANNER_DIR / f"{key}.json"
    if data_file.exists() and meta_file.exists():
        mime = json.loads(meta_file.read_text(encoding="utf-8"))["mime"]
        return data_file.read_bytes(), mime
    if not allow_download:
        return None
    image_url = find_banner_image(post_url)
    if not image_url:
        return None
    data, mime = download_image(image_url)
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    data_file.write_bytes(data)
    meta_file.write_text(json.dumps({"mime": mime, "post": post_url}), encoding="utf-8")
    return data, mime


def fetch_feed_text(url, max_age_days=45):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    parts, images = [], []
    rate_limited = False
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

        date_text = published.astimezone(MYT).date().isoformat() if published else "unknown"
        parts.append(f"Title: {entry.title}\nPublished: {date_text}\nLink: {entry.link}\n{body}")

        if not wants_banner(body):
            continue
        try:
            banner = get_banner(entry.link, allow_download=not rate_limited)
        except RateLimited:
            rate_limited = True
            print("Site is rate-limiting us: skipping new banner downloads this time (saved ones are still used).")
            continue
        except Exception as e:
            print(f"Couldn't get banner for '{entry.title}': {e}")
            continue
        if banner:
            data, mime = banner
            images.append({"label": entry.title, "data": data, "mime": mime})

    return "\n\n---\n\n".join(parts), images

LUMA_LINK = re.compile(r"https://luma\.com/\S+")


def to_myt(value):
    if isinstance(value, datetime):
        return value.astimezone(MYT)
    return datetime(value.year, value.month, value.day, tzinfo=MYT)  # all-day event (date only)


def fetch_ical_bytes(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.content


def parse_ical_events(data, after=None):
    calendar = Calendar.from_ical(data)
    events = []
    for item in calendar.walk("VEVENT"):
        raw_start = item.decoded("DTSTART")
        all_day = not isinstance(raw_start, datetime)  # a date with no time
        start = to_myt(raw_start)
        if item.get("DTEND"):
            raw_end = item.decoded("DTEND")
            if all_day:
                last_day = raw_end - timedelta(days=1)  # iCal all-day end dates are the day AFTER
                end = datetime(last_day.year, last_day.month, last_day.day, 23, 59, tzinfo=MYT)
            else:
                end = to_myt(raw_end)
        else:
            end = start
        if after and end < after:
            continue  # already finished

        description = str(item.get("DESCRIPTION", ""))
        location = str(item.get("LOCATION", "")).strip() or None
        uid = str(item.get("UID", ""))
        event_id = uid.split("@")[0]

        if event_id.startswith("evt-"):
            link = f"https://luma.com/event/{event_id}"  # Luma's permanent page for this exact event
        elif location and location.startswith("http"):
            link = location  # listed on Luma but hosted on another website
        else:
            match = LUMA_LINK.search(description)
            link = match.group(0) if match else None

        if location and location.startswith("http"):
            location = None  # a link, not a venue (hidden until you register, or hosted elsewhere)
        organizer = item.get("ORGANIZER")

        events.append({
            "uid": uid,
            "title": str(item.get("SUMMARY", "")).strip(),
            "start": start,
            "end": end,
            "all_day": all_day,
            "location": location,
            "link": link,
            "host": organizer.params.get("CN") if organizer is not None else None,
            "description": description,
        })
    return events


def fetch_ical_events(url):
    return parse_ical_events(fetch_ical_bytes(url), after=datetime.now(MYT))

def parse_jsonld_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

TOPIC_WORDS = [  # checked in order; the first match wins
    ("Security", ["security", "infosec", "cyber"]),
    ("Cloud & DevOps", ["cloud", "devops", "kubernetes"]),
    ("Data", ["data", "analytics"]),
    ("AI", ["artificial intelligence", "(ai)", " ai ", "machine learning"]),
    ("Web & Mobile", ["web", "mobile", "javascript", "android", "ios"]),
    ("Design", ["design", "ux"]),
]

def topic_from_text(text):
    lowered = f" {text.lower()} "
    for topic, words in TOPIC_WORDS:
        if any(word in lowered for word in words):
            return topic
    return "Other tech"

def fetch_jsonld_events(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    now = datetime.now(MYT)
    events = []
    for block in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(block.string or "")
        except json.JSONDecodeError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if not isinstance(item, dict) or not str(item.get("@type", "")).endswith("Event"):
                continue  # breadcrumbs and other non-event data
            if "Online" in str(item.get("eventAttendanceMode", "")):
                continue  # online events are listed on every city page, not just Malaysia's

            raw_start = parse_jsonld_time(item["startDate"])
            raw_end = parse_jsonld_time(item.get("endDate") or item["startDate"])
            all_day = (raw_start.hour, raw_start.minute) == (0, 0) and (raw_end.hour, raw_end.minute) == (0, 0)
            if all_day:  # dates given as midnight UTC really mean whole days
                start = datetime(raw_start.year, raw_start.month, raw_start.day, tzinfo=MYT)
                end = datetime(raw_end.year, raw_end.month, raw_end.day, 23, 59, tzinfo=MYT)  # end date is inclusive here
            else:
                start, end = raw_start.astimezone(MYT), raw_end.astimezone(MYT)
            if end < now:
                continue  # already finished

            place = item.get("location") if isinstance(item.get("location"), dict) else {}
            events.append({
                "uid": item.get("url") or item["name"],
                "title": item["name"],
                "start": start,
                "end": end,
                "all_day": all_day,
                "location": place.get("name"),
                "link": item.get("url"),
                "host": None,
                "description": item.get("description", ""),
                "topic": topic_from_text(item.get("description", "")),
            })
    return events