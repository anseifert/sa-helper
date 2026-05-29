from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import structlog

_logger = structlog.get_logger()
DEFAULT_TIMEZONE = "America/New_York"


def resolve_timezone(tz_name: str | None) -> str:
    """Return a valid IANA timezone name; fall back if missing or unknown."""
    name = (tz_name or DEFAULT_TIMEZONE).strip()
    try:
        ZoneInfo(name)
        return name
    except ZoneInfoNotFoundError:
        _logger.warning("invalid_timezone_fallback", requested=name, fallback=DEFAULT_TIMEZONE)
        try:
            ZoneInfo(DEFAULT_TIMEZONE)
            return DEFAULT_TIMEZONE
        except ZoneInfoNotFoundError:
            return "UTC"


def sql_utc_now() -> datetime:
    """Naive UTC for SQLite comparisons (avoids aware/naive errors)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sql_utc_days_ago(days: int) -> datetime:
    return sql_utc_now() - timedelta(days=days)


def as_sqlite_utc(dt: datetime | None) -> datetime | None:
    """Normalize any datetime to naive UTC for safe SQLite comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
