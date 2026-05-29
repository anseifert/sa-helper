from app.services.calendar_today import _meeting_from_event, _parse_event_end
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


def test_meeting_all_redhat_excluded():
    ev = {
        "summary": "Internal",
        "start": {"dateTime": "2026-05-22T15:00:00Z"},
        "attendees": [{"email": "a@redhat.com"}, {"email": "b@redhat.com"}],
    }
    assert _meeting_from_event(ev, "redhat.com") is None
