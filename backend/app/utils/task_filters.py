"""Exclude calendar invites/updates from Tasks; calendar lives on Today's meetings only."""

import re

# Synced from Google Calendar extractor
CALENDAR_SOURCES = frozenset({"calendar"})

# Task types produced only from calendar sync
CALENDAR_ONLY_TASK_TYPES = frozenset({"calendar_action"})

# Gmail / notification subjects for calendar invites and updates
_CALENDAR_INVITE_SUBJECT = re.compile(
    r"^\s*("
    r"invitation|updated invitation|accepted|declined|"
    r"canceled event|cancelled event|"
    r"notification:\s*.+@|"
    r"new time proposed|"
    r"event (updated|canceled|cancelled)"
    r")\s*:?",
    re.I,
)
_CALENDAR_MAILER = re.compile(
    r"calendar-notification@google\.com|"
    r"google\.com|"
    r"resource\.calendar@google\.com",
    re.I,
)


def is_gmail_calendar_notification(
    *,
    subject: str = "",
    from_header: str = "",
    snippet: str = "",
) -> bool:
    """True for Google Calendar invitation/update emails in Gmail."""
    subj = subject or ""
    if _CALENDAR_INVITE_SUBJECT.search(subj):
        return True
    if _CALENDAR_MAILER.search(from_header or ""):
        return True
    combined = f"{subj} {snippet}"
    if re.search(r"\bcalendar invite\b", combined, re.I):
        return True
    if re.search(r"\b(has invited you|invited you to)\b", combined, re.I) and re.search(
        r"\b(event|meeting|calendar)\b", combined, re.I
    ):
        return True
    return False


def is_calendar_task(
    *,
    source: str,
    badge_source: str | None = None,
    task_type: str,
    title: str = "",
    description: str | None = None,
    from_header: str = "",
) -> bool:
    """True if this open task should not appear on the Tasks page."""
    if source in CALENDAR_SOURCES:
        return True
    if (badge_source or "") == "calendar":
        return True
    if task_type in CALENDAR_ONLY_TASK_TYPES:
        return True
    if task_type == "schedule_meeting" and source == "gmail":
        return is_gmail_calendar_notification(
            subject=title,
            from_header=from_header,
            snippet=description or "",
        )
    if is_gmail_calendar_notification(subject=title, snippet=description or ""):
        return True
    return False
