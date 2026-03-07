"""UTC timestamp helpers. All timestamps stored as ISO 8601 UTC."""

from datetime import datetime, timezone


def utcnow() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 UTC timestamp string to a datetime object.

    Accepts formats with 'Z' suffix or '+00:00' offset.
    """
    cleaned = value.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


def to_iso(dt: datetime) -> str:
    """Convert a datetime to ISO 8601 UTC string.

    If the datetime is naive, it is assumed to be UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
