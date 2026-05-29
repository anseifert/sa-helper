import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityAccount:
    key: str
    display_name: str
    patterns: tuple[str, ...]


PRIORITY_ACCOUNTS: tuple[PriorityAccount, ...] = (
    PriorityAccount(
        "exxonmobil",
        "ExxonMobil",
        (r"exxon", r"exxonmobil", r"xom\.com", r"exxonmobil\.com"),
    ),
    PriorityAccount(
        "conocophillips",
        "ConocoPhillips",
        (r"conoco", r"conocophillips", r"cop\.com", r"conocophillips\.com"),
    ),
    PriorityAccount(
        "windstream_uniti",
        "Windstream / Uniti",
        (r"windstream", r"uniti", r"uniti\.com", r"windstream\.com"),
    ),
    PriorityAccount(
        "epp",
        "Enterprise Partner Products (EPP)",
        (
            r"\bepp\b",
            r"\beprod\b",
            r"enterprise\s+partner",
            r"enterprise\s+product",
            r"eprod\.io",
        ),
    ),
)

_ACCOUNT_ORDER = {a.key: i for i, a in enumerate(PRIORITY_ACCOUNTS)}


def match_priority_account(
    *,
    company_name: str | None = None,
    company_domain: str | None = None,
    title: str = "",
    description: str = "",
) -> str | None:
    haystack = " ".join(
        filter(None, [company_name, company_domain, title, description])
    ).lower()
    if not haystack:
        return None
    for account in PRIORITY_ACCOUNTS:
        for pattern in account.patterns:
            if re.search(pattern, haystack, re.I):
                return account.key
    return None


def priority_display_name(key: str) -> str:
    for account in PRIORITY_ACCOUNTS:
        if account.key == key:
            return account.display_name
    return key


def priority_sort_key(key: str) -> int:
    return _ACCOUNT_ORDER.get(key, 999)


def tasks_section_id_for_company(company_name: str) -> str:
    """Stable section id used on /tasks?section=… (matches Tasks page grouping)."""
    key = match_priority_account(company_name=company_name)
    if key:
        return key
    name = (company_name or "Unassigned").strip()
    if name.lower() == "unassigned":
        return "unassigned"
    return name.lower().replace(" ", "_")
