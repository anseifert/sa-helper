import json
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.models.task import Task, TaskContact
from app.schemas.task_exclusions import TaskExclusionsOut, TaskExclusionsUpdate
from app.utils.domain import email_domain

SETTING_KEY = "dashboard_task_exclusions"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str | None:
    v = value.strip().lower()
    if not v or not _EMAIL_RE.match(v):
        return None
    return v


def normalize_company_target(value: str) -> str | None:
    v = value.strip()
    if not v:
        return None
    if "@" in v:
        dom = email_domain(v)
        return dom.lower() if dom else None
    if "." in v and " " not in v:
        return v.lower()
    return v.lower()


def _parse_raw(raw: str | None) -> TaskExclusionsOut:
    if not raw:
        return TaskExclusionsOut()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return TaskExclusionsOut()
    emails: list[str] = []
    companies: list[str] = []
    for e in data.get("emails") or []:
        norm = normalize_email(str(e))
        if norm and norm not in emails:
            emails.append(norm)
    for c in data.get("companies") or []:
        norm = normalize_company_target(str(c))
        if norm and norm not in companies:
            companies.append(norm)
    return TaskExclusionsOut(emails=emails, companies=companies)


async def load_task_exclusions(session: AsyncSession) -> TaskExclusionsOut:
    row = await session.get(Setting, SETTING_KEY)
    return _parse_raw(row.value if row else None)


async def save_task_exclusions(
    session: AsyncSession, body: TaskExclusionsUpdate
) -> TaskExclusionsOut:
    emails: list[str] = []
    for e in body.emails:
        norm = normalize_email(e)
        if norm and norm not in emails:
            emails.append(norm)
    companies: list[str] = []
    for c in body.companies:
        norm = normalize_company_target(c)
        if norm and norm not in companies:
            companies.append(norm)
    out = TaskExclusionsOut(emails=emails, companies=companies)
    payload = json.dumps({"emails": out.emails, "companies": out.companies})
    row = await session.get(Setting, SETTING_KEY)
    if row:
        row.value = payload
    else:
        session.add(Setting(key=SETTING_KEY, value=payload))
    await session.flush()
    return out


def task_matches_exclusion(task: Task, rules: TaskExclusionsOut) -> bool:
    if not rules.emails and not rules.companies:
        return False

    email_set = set(rules.emails)
    if email_set:
        for link in task.contacts or []:
            contact = link.contact
            if contact and contact.email.lower() in email_set:
                return True

    if rules.companies:
        company_targets = set(rules.companies)
        company = task.company
        if company:
            name_key = company.name.lower()
            domain_key = company.domain.lower()
            if name_key in company_targets or domain_key in company_targets:
                return True
            for target in company_targets:
                if " " in target or "." not in target:
                    if target in name_key or name_key in target:
                        return True
        for link in task.contacts or []:
            contact = link.contact
            if not contact:
                continue
            dom = email_domain(contact.email)
            if dom and dom in company_targets:
                return True
    return False
