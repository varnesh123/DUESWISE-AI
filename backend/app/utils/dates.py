"""Date and timestamp helpers — ISO dates, timezone-aware UTC timestamps."""

from datetime import date, datetime, timedelta, timezone
import re

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None

try:
    IST = ZoneInfo("Asia/Kolkata") if ZoneInfo else None
except Exception:  # zoneinfo database may lack Asia/Kolkata on some systems
    IST = None

# Fixed offset fallback for Asia/Kolkata (UTC+5:30) when zoneinfo data is missing.
IST_FALLBACK = timezone(timedelta(hours=5, minutes=30))
IST_TZ = IST or IST_FALLBACK


def parse_date_iso(date_str: str) -> date:
    """Parse a YYYY-MM-DD string into a date."""
    return date.fromisoformat(date_str.strip())


def parse_indian_date(date_str: str) -> date:
    """Parse common Indian date formats.

    Supports: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, DD-MM-YY, DD/MM/YY.
    Falls back to ISO parsing.
    """
    date_str = date_str.strip()
    if not date_str:
        raise ValueError("Date string is empty")

    # ISO format first
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        pass

    # DD-MM-YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(year, month, day)

    # DD-MM-YY or DD/MM/YY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2})$", date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(2000 + year, month, day)

    raise ValueError(f"Cannot parse date: {date_str!r}")


def format_date_iso(d: date) -> str:
    """Format a date as YYYY-MM-DD."""
    return d.isoformat()


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_z(dt: datetime) -> str:
    """Format a datetime as ISO-8601 UTC with Z suffix."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
