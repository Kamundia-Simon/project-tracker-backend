"""The single source of 'now' and of the timezone our commitments are quoted in."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Every client-facing time in this app is a UK time. A named zone, not a fixed
# offset, because the UK moves between GMT and BST twice a year.
BUSINESS_TZ = ZoneInfo("Europe/London")


def utcnow() -> datetime:
    """Current instant in UTC, naive — the shape our DATETIME columns store and return."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def business_now() -> datetime:
    """Current instant expressed in UK time — for day boundaries, never for storage."""
    return datetime.now(BUSINESS_TZ)


def to_utc(value: datetime) -> datetime:
    """Normalise an incoming datetime to UTC, treating a naive value as UK time."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=BUSINESS_TZ)
    return value.astimezone(timezone.utc)


def to_db(value: datetime) -> datetime:
    """Normalise any incoming datetime to naive UTC for storage."""
    return to_utc(value).replace(tzinfo=None)