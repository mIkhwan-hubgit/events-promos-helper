from schema import Promo


def to_promo(event):
    start, end = event["start"], event["end"]
    when = f"{start:%a %d %b, %I:%M %p}"
    when += f" to {end:%I:%M %p}" if end.date() == start.date() else f" to {end:%a %d %b}"
    details = when + (f" · Hosted by {event['host']}" if event["host"] else "")
    return Promo(
        title=event["title"],
        details=details,
        start_date=start.date().isoformat(),
        end_date=end.date().isoformat(),
        location=event["location"],
        channel=None,
        link=event["link"],
    )