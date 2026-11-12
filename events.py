from schema import EventItem


def to_promo(event):
    start, end = event["start"], event["end"]
    if event.get("all_day"):
        same_day = start.date() == end.date()
        when = f"{start:%a %d %b}" if same_day else f"{start:%a %d %b} to {end:%a %d %b}"
        when += " (all day)"
    else:
        when = f"{start:%a %d %b, %I:%M %p}"
        when += f" to {end:%I:%M %p}" if end.date() == start.date() else f" to {end:%a %d %b}"

    extras = []
    if event.get("host"):
        extras.append(f"Hosted by {event['host']}")
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