"""Gmail recipient rules: USER_EMAIL in To or Cc; exclude Google Groups."""

from __future__ import annotations

import re
from email.utils import getaddresses

_GOOGLE_GROUP_DOMAINS = frozenset({"googlegroups.com", "groups.google.com"})
_EMAIL_FALLBACK = re.compile(r"[\w.+-]+@[\w.-]+\.\w+", re.I)


def parse_address_header(header: str) -> list[str]:
    """Return lowercased emails parsed from a To or Cc header."""
    raw = (header or "").strip()
    if not raw:
        return []
    seen: list[str] = []
    for _name, addr in getaddresses([raw]):
        normalized = (addr or "").strip().lower()
        if normalized and "@" in normalized and normalized not in seen:
            seen.append(normalized)
    if seen:
        return seen
    for match in _EMAIL_FALLBACK.finditer(raw):
        addr = match.group(0).lower()
        if addr not in seen:
            seen.append(addr)
    return seen


def parse_to_addresses(to_header: str) -> list[str]:
    """Backward-compatible alias for To-only parsing."""
    return parse_address_header(to_header)


def is_google_group_email(email: str) -> bool:
    domain = (email or "").rsplit("@", 1)[-1].lower()
    return domain in _GOOGLE_GROUP_DOMAINS


def headers_indicate_google_group(
    *,
    list_id: str = "",
    list_unsubscribe: str = "",
) -> bool:
    """Detect Google Groups list traffic from List-* headers."""
    blob = f"{list_id or ''} {list_unsubscribe or ''}".lower()
    return "googlegroups.com" in blob or "groups.google" in blob


def user_in_to_or_cc(
    to_header: str,
    cc_header: str,
    user_email: str,
) -> bool:
    """True when ``user_email`` is a parsed address in To or Cc."""
    user = (user_email or "").strip().lower()
    if not user:
        return False
    recipients = parse_address_header(to_header) + parse_address_header(cc_header)
    return user in recipients


def recipients_include_google_group(to_header: str, cc_header: str = "") -> bool:
    addrs = parse_address_header(to_header) + parse_address_header(cc_header)
    return any(is_google_group_email(addr) for addr in addrs)


def gmail_to_eligible_for_tasks(
    *,
    to_header: str,
    cc_header: str = "",
    user_email: str,
    list_id: str = "",
    list_unsubscribe: str = "",
) -> bool:
    """
    Gmail threads qualify when USER_EMAIL is in To or Cc and the message
    was not sent to a Google Group (in To/Cc or via list headers).
    """
    user = (user_email or "").strip().lower()
    if not user:
        return True
    if headers_indicate_google_group(list_id=list_id, list_unsubscribe=list_unsubscribe):
        return False
    if recipients_include_google_group(to_header, cc_header):
        return False
    return user_in_to_or_cc(to_header, cc_header, user)


def gmail_task_metadata(
    *,
    to_header: str,
    cc_header: str = "",
    user_email: str,
    list_id: str = "",
    list_unsubscribe: str = "",
) -> dict:
    eligible = gmail_to_eligible_for_tasks(
        to_header=to_header,
        cc_header=cc_header,
        user_email=user_email,
        list_id=list_id,
        list_unsubscribe=list_unsubscribe,
    )
    has_group = recipients_include_google_group(
        to_header, cc_header
    ) or headers_indicate_google_group(list_id=list_id, list_unsubscribe=list_unsubscribe)
    return {
        "gmail_to_eligible": eligible,
        "user_in_recipients": user_in_to_or_cc(to_header, cc_header, user_email),
        "to_has_google_group": has_group,
        "to_addresses": parse_address_header(to_header)[:25],
        "cc_addresses": parse_address_header(cc_header)[:25],
    }
