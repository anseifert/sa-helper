from datetime import datetime, timezone

from app.utils.datetime_util import as_sqlite_utc


def test_as_sqlite_utc_from_aware():
    aware = datetime(2020, 6, 1, 12, 0, tzinfo=timezone.utc)
    naive = as_sqlite_utc(aware)
    assert naive is not None
    assert naive.tzinfo is None
    assert naive.year == 2020


def test_as_sqlite_utc_naive_unchanged():
    naive = datetime(2020, 6, 1)
    assert as_sqlite_utc(naive) == naive
