"""Filter calendar events by attendee email domain (Red Hat internal vs external)."""

from app.utils.domain import email_domain

INTERNAL_DOMAIN = "redhat.com"


def internal_email_domain(user_email: str | None) -> str:
    """Domain treated as internal; defaults to redhat.com."""
    if user_email:
        dom = email_domain(user_email)
        if dom:
            return dom.lower()
    return INTERNAL_DOMAIN


def collect_event_emails(event: dict) -> set[str]:
    emails: set[str] = set()
    for attendee in event.get("attendees") or []:
        raw = (attendee.get("email") or "").strip().lower()
        if raw:
            emails.add(raw)
    for key in ("organizer", "creator"):
        raw = (event.get(key) or {}).get("email", "").strip().lower()
        if raw:
            emails.add(raw)
    return emails


def external_attendee_emails(event: dict, internal_domain: str = INTERNAL_DOMAIN) -> list[str]:
    domain = internal_domain.lower()
    suffix = f"@{domain}"
    return sorted(e for e in collect_event_emails(event) if not e.endswith(suffix))


def meeting_has_external_attendee(event: dict, internal_domain: str = INTERNAL_DOMAIN) -> bool:
    """True when at least one participant email is outside the internal domain."""
    emails = collect_event_emails(event)
    if not emails:
        return False
    domain = internal_domain.lower()
    suffix = f"@{domain}"
    return any(not e.endswith(suffix) for e in emails)
