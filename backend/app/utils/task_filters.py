"""Exclude calendar invites and noisy subjects from Tasks; calendar on Today's meetings only."""

import json
import re

# Synced from Google Calendar extractor
CALENDAR_SOURCES = frozenset({"calendar"})

# Task types produced only from calendar sync
CALENDAR_ONLY_TASK_TYPES = frozenset({"calendar_action"})

# Email subjects to drop from Tasks (case-insensitive, start of subject line)
EXCLUDED_SUBJECT_PREFIXES = ("re:", "notes", "invitation")
# Substrings anywhere in the subject line
EXCLUDED_SUBJECT_PHRASES = ("team deno weekly",)

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
    r"resource\.calendar@google\.com",
    re.I,
)


def task_subject_line(title: str) -> str:
    """Gmail tasks use ``{Subject} — {suffix}``; return the subject portion."""
    return (title or "").split(" — ", 1)[0].strip()


def is_excluded_subject(title: str = "", description: str | None = None) -> bool:
    """True when the email subject should not appear as a task."""
    line = task_subject_line(title)
    if not line and description:
        line = (description or "").split("\n", 1)[0].strip()[:200]
    lower = line.lower()
    if any(lower.startswith(prefix) for prefix in EXCLUDED_SUBJECT_PREFIXES):
        return True
    return any(phrase in lower for phrase in EXCLUDED_SUBJECT_PHRASES)


def is_gmail_calendar_notification(
    *,
    subject: str = "",
    from_header: str = "",
    snippet: str = "",
) -> bool:
    """True for Google Calendar invitation/update emails in Gmail."""
    if is_excluded_subject(subject):
        return True
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


def is_ineligible_gmail_recipient(
    *,
    source: str,
    metadata_json: str | None,
    user_email: str = "",
) -> bool:
    """True when a Gmail task should be hidden (To / Google Groups rules)."""
    if source != "gmail":
        return False
    user = (user_email or "").strip().lower()
    if not user:
        return False
    if not metadata_json:
        return True
    try:
        meta = json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return True
    if meta.get("gmail_to_eligible") is True:
        return False
    if meta.get("gmail_to_eligible") is False:
        return True
    in_recipients = meta.get("user_in_recipients") or meta.get("user_in_to")
    if in_recipients and not meta.get("to_has_google_group"):
        return False
    return True


def is_calendar_task(
    *,
    source: str,
    badge_source: str | None = None,
    task_type: str,
    title: str = "",
    description: str | None = None,
    from_header: str = "",
    metadata_json: str | None = None,
    user_email: str = "",
) -> bool:
    """True if this open task should not appear on the Tasks page."""
    if is_ineligible_gmail_recipient(
        source=source, metadata_json=metadata_json, user_email=user_email
    ):
        return True
    if is_excluded_subject(title, description):
        return True
    if source in CALENDAR_SOURCES:
        return True
    if (badge_source or "") == "calendar":
        return True
    if task_type in CALENDAR_ONLY_TASK_TYPES:
        return True
    if task_type == "schedule_meeting" and source == "gmail":
        return is_gmail_calendar_notification(
            subject=task_subject_line(title) or title,
            from_header=from_header,
            snippet=description or "",
        )
    if is_gmail_calendar_notification(
        subject=task_subject_line(title) or title,
        snippet=description or "",
    ):
        return True
    return False
