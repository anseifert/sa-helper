import re
from datetime import datetime, timedelta, timezone

MEETING_WORDS = re.compile(
    r"\b(meeting|call|zoom|teams|webex|schedule|calendar invite|sync up|catch up)\b",
    re.I,
)
DOC_WORDS = re.compile(
    r"\b(document|doc|proposal|deck|deliverable|attachment|send over|share the)\b",
    re.I,
)
DATA_WORDS = re.compile(r"\b(data|report|metrics|numbers|spreadsheet|csv)\b", re.I)
ASK_WORDS = re.compile(
    r"\b(can you|could you|please|need you to|would you|let me know|follow up|waiting)\b",
    re.I,
)
QUESTION = re.compile(r"\?|^\s*(what|when|where|how|why|who)\b", re.I | re.M)
CONCUR_WORDS = re.compile(
    r"\b(concur|sap concur|expense report|payment request|reimbursement|"
    r"expense approval|approve.{0,20}expense)\b",
    re.I,
)
REDHAT_ACTION = re.compile(
    r"\b(feedback|action required|please review|your input|respond by|"
    r"needs your attention|follow up|duty|duties|approval needed|"
    r"please respond|waiting on you|rsvp)\b",
    re.I,
)
REDHAT_NOISE = re.compile(
    r"\b(newsletter|digest|all-hands|office hours|webinar|training invite)\b",
    re.I,
)


def parse_email_date(header_value: str | None) -> datetime | None:
    if not header_value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(header_value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def is_from_user(from_header: str, user_email: str) -> bool:
    return user_email.lower() in (from_header or "").lower()


def external_participants(headers: dict[str, str], user_email: str, user_domain: str) -> list[str]:
    emails: set[str] = set()
    for key in ("From", "To", "Cc"):
        raw = headers.get(key, "")
        for match in re.finditer(r"[\w.+-]+@[\w.-]+\.\w+", raw):
            addr = match.group(0).lower()
            if user_email.lower() not in addr and not addr.endswith(f"@{user_domain}"):
                emails.add(addr)
    return list(emails)


def classify_gmail_thread(
    *,
    user_email: str,
    user_domain: str,
    last_from_user: bool,
    last_message_at: datetime | None,
    subject: str,
    snippet: str,
    has_user_reply_after_customer: bool,
    customer_asked_no_reply: bool,
    stale_days: int = 7,
) -> list[tuple[str, str]]:
    """Return list of (task_type, title_suffix)."""
    results: list[tuple[str, str]] = []
    text = f"{subject} {snippet}"
    now = datetime.now(timezone.utc)

    if customer_asked_no_reply:
        results.append(("customer_ask_pending", "Reply to customer request"))
    elif not last_from_user and ASK_WORDS.search(text):
        results.append(("user_owes_reply", "You owe a reply"))
    elif not last_from_user and QUESTION.search(snippet):
        results.append(("user_owes_reply", "Answer customer question"))

    if MEETING_WORDS.search(text):
        results.append(("schedule_meeting", "Schedule or confirm meeting"))
    if DOC_WORDS.search(text):
        results.append(("send_docs", "Send documents or deliverables"))
    if DATA_WORDS.search(text):
        results.append(("send_data", "Provide data or report"))

    if (
        last_from_user
        and last_message_at
        and (now - last_message_at) >= timedelta(days=stale_days)
    ):
        results.append(("stale_thread", f"No reply in {stale_days}+ days"))

    return results


def classify_concur_message(*, subject: str, snippet: str, from_header: str) -> list[tuple[str, str]]:
    text = f"{subject} {snippet} {from_header}"
    if not CONCUR_WORDS.search(text):
        return []
    return [("concur_payment", "Concur / expense action needed")]


def classify_redhat_direct(
    *,
    user_email: str,
    from_header: str,
    to_header: str,
    subject: str,
    snippet: str,
    last_from_user: bool,
) -> list[tuple[str, str]]:
    if last_from_user:
        return []
    if "redhat.com" not in (from_header or "").lower():
        return []
    if user_email.lower() not in (to_header or "").lower():
        return []
    if REDHAT_NOISE.search(f"{subject} {snippet}"):
        return []
    text = f"{subject} {snippet}"
    if REDHAT_ACTION.search(text) or QUESTION.search(snippet) or ASK_WORDS.search(text):
        return [("redhat_attention", "Red Hat email needs your attention")]
    return []
