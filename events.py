import re
from datetime import date, datetime

import clock
from schema import EventItem


def concerts_to_events(concerts, page_url, venue):
    now = clock.now()
    events = []
    for concert in concerts:
        try:
            first_day = date.fromisoformat(concert["start_date"])
            last_day = date.fromisoformat(concert.get("end_date") or concert["start_date"])
        except (TypeError, ValueError):
            continue  # no usable date, so we can't place it on the calendar

        hour, minute, timed = 0, 0, False
        if concert.get("time"):
            try:
                hour, minute = (int(part) for part in concert["time"].split(":"))
                timed = True
            except ValueError:
                pass  # unreadable time: treat as an all-day listing

        start = datetime(first_day.year, first_day.month, first_day.day, hour, minute, tzinfo=clock.MYT)
        if last_day > first_day or not timed:
            end = datetime(last_day.year, last_day.month, last_day.day, 23, 59, tzinfo=clock.MYT)
        else:
            end = start  # one performance; the page doesn't say when it ends, so we don't guess
        if end < now:
            continue  # already happened

        # every concert shares the season page's address, so add a unique tag to tell them apart
        slug = re.sub(r"[^a-z0-9]+", "-", concert["title"].lower()).strip("-")
        events.append({
            "title": concert["title"],
            "start": start,
            "end": end,
            "all_day": not timed,
            "location": venue,
            "link": f"{page_url}#{slug}-{first_day.isoformat()}",
            "host": None,
            "info": concert.get("info"),
            "description": concert.get("info") or "",
        })
    return events


def to_promo(event):
    start, end = event["start"], event["end"]
    day = "%a %d %b" if start.year == clock.today().year else "%a %d %b %Y"  # add the year only when it isn't this year
    if event.get("all_day"):
        same_day = start.date() == end.date()
        when = f"{start:{day}}" if same_day else f"{start:{day}} to {end:{day}}"
        when += " (all day)"
    else:
        when = f"{start:{day}, %I:%M %p}"
        if end.date() != start.date():
            when += f" to {end:{day}}"
        elif end > start:
            when += f" to {end:%I:%M %p}"

    extras = []
    if event.get("host"):
        extras.append(f"Hosted by {event['host']}")
    if event.get("info"):
        extras.append(event["info"])
    if event.get("price"):
        extras.append(event["price"])

    return EventItem(
        title=event["title"],
        details=" · ".join([when] + extras),
        start_date=start.date().isoformat(),
        end_date=end.date().isoformat(),
        location=event["location"],
        channel=None,
        link=event["link"],
        topic=event.get("topic"),
        category=event.get("category"),
    )