import re

COMMON_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "icloud.com",
        "proton.me",
        "protonmail.com",
    }
)


def email_domain(email: str) -> str | None:
    if "@" not in email:
        return None
    return email.rsplit("@", 1)[-1].lower().strip()


def domain_to_company_name(domain: str) -> str:
    """Derive display company name from email domain."""
    base = domain.split(".")[0]
    return base.replace("-", " ").title()


def is_consumer_domain(domain: str) -> bool:
    return domain.lower() in COMMON_DOMAINS


def company_key_for_email(email: str, user_domain: str | None = None) -> str | None:
    domain = email_domain(email)
    if not domain:
        return None
    if is_consumer_domain(domain):
        return email.lower()
    if user_domain and domain == user_domain.lower():
        return None  # internal — no company bucket
    return domain
