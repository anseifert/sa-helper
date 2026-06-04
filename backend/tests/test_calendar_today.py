from datetime import datetime, timedelta, timezone

from app.schemas.dashboard import TodayMeetingOut
from app.services.calendar_today import (
    _meeting_from_event,
    _parse_event_end,
    drop_overdue_meetings,
    meeting_is_overdue,
)
from app.utils.datetime_util import resolve_timezone


def test_resolve_timezone_fallback():
    assert resolve_timezone("America/New_York") == "America/New_York"
    assert resolve_timezone("Not/A_Real_Zone") in ("America/New_York", "UTC")


def test_parse_event_end_missing_returns_none():
    assert _parse_event_end({"dateTime": "not-a-date"}) is None


def test_meeting_from_event_end_optional():
    ev = {
        "summary": "Customer call",
        "start": {"dateTime": "2026-05-22T15:00:00Z"},
        "end": {"dateTime": "bad"},
        "attendees": [
            {"email": "you@redhat.com"},
            {"email": "them@acme.com"},
        ],
    }
    meeting = _meeting_from_event(ev, "redhat.com")
    assert meeting is not None
    assert meeting.end_at is None
    assert "them@acme.com" in meeting.external_emails


def test_meeting_is_overdue():
    now = datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc)
    past = TodayMeetingOut(
        event_id="1",
        title="Done",
        start_at="2026-05-22T14:00:00+00:00",
        end_at="2026-05-22T15:00:00+00:00",
        external_emails=["a@b.com"],
        html_link=None,
    )
    future = TodayMeetingOut(
        event_id="2",
        title="Later",
        start_at="2026-05-22T17:00:00+00:00",
        end_at="2026-05-22T18:00:00+00:00",
        external_emails=["a@b.com"],
        html_link=None,
    )
    assert meeting_is_overdue(past, now=now)
    assert not meeting_is_overdue(future, now=now)
    kept = drop_overdue_meetings([past, future], now=now)
    assert len(kept) == 1
    assert kept[0].event_id == "2"


def test_meeting_overdue_without_end_uses_one_hour():
    now = datetime(2026, 5, 22, 16, 0, tzinfo=timezone.utc)
    m = TodayMeetingOut(
        event_id="3",
        title="No end",
        start_at=(now - timedelta(hours=2)).isoformat(),
        end_at=None,
        external_emails=["a@b.com"],
        html_link=None,
    )
    assert meeting_is_overdue(m, now=now)


def test_meeting_all_redhat_excluded():
    ev = {
        "summary": "Internal",
        "start": {"dateTime": "2026-05-22T15:00:00Z"},
        "attendees": [{"email": "a@redhat.com"}, {"email": "b@redhat.com"}],
    }
    assert _meeting_from_event(ev, "redhat.com") is None
