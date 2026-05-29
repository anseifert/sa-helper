from datetime import datetime, timedelta, timezone


def sql_utc_now() -> datetime:
    """Naive UTC for SQLite comparisons (avoids aware/naive errors)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def sql_utc_days_ago(days: int) -> datetime:
    return sql_utc_now() - timedelta(days=days)


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
