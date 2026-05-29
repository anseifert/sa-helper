from app.utils.calendar_filter import (
    collect_event_emails,
    external_attendee_emails,
    meeting_has_external_attendee,
)


def _event(attendees: list[str], organizer: str | None = None) -> dict:
    ev: dict = {
        "attendees": [{"email": e} for e in attendees],
    }
    if organizer:
        ev["organizer"] = {"email": organizer}
    return ev


def test_all_redhat_excluded():
    ev = _event(["alice@redhat.com", "bob@redhat.com"], "alice@redhat.com")
    assert not meeting_has_external_attendee(ev, "redhat.com")
    assert external_attendee_emails(ev, "redhat.com") == []


def test_external_included():
    ev = _event(["alice@redhat.com", "partner@acme.com"])
    assert meeting_has_external_attendee(ev, "redhat.com")
    assert external_attendee_emails(ev, "redhat.com") == ["partner@acme.com"]


def test_no_attendees_excluded():
    assert not meeting_has_external_attendee({})
    assert collect_event_emails({}) == set()


def test_organizer_external_counts():
    ev = _event([], organizer="guest@vendor.io")
    assert meeting_has_external_attendee(ev, "redhat.com")
    assert "guest@vendor.io" in external_attendee_emails(ev, "redhat.com")
