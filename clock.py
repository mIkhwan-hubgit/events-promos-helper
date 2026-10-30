from datetime import datetime, timedelta, timezone

MYT = timezone(timedelta(hours=8))  # Malaysia time, UTC+8 (no daylight saving)


def now():
    return datetime.now(MYT)


def today():
    return now().date()

def parse(value):
    t = datetime.fromisoformat(value)
    return t if t.tzinfo else t.replace(tzinfo=MYT)  # old saved times without a zone count as Malaysia time