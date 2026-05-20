from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.utils.domain import domain_to_company_name, email_domain, is_consumer_domain


async def get_or_create_company(
    session: AsyncSession, domain_or_key: str, override_name: str | None = None
) -> Company | None:
    if not domain_or_key:
        return None
    key = domain_or_key.lower()
    result = await session.execute(select(Company).where(Company.domain == key))
    company = result.scalar_one_or_none()
    if company:
        if override_name and company.name != override_name:
            company.name = override_name
        return company
    name = override_name or (
        domain_or_key if is_consumer_domain(key) else domain_to_company_name(key)
    )
    company = Company(name=name, domain=key)
    session.add(company)
    await session.flush()
    return company


async def resolve_company_for_email(
    session: AsyncSession,
    email: str,
    company_override: str | None = None,
    user_domain: str | None = None,
) -> Company | None:
    if company_override:
        return await get_or_create_company(session, company_override.lower(), company_override)
    domain = email_domain(email)
    if not domain:
        return None
    if user_domain and domain == user_domain.lower():
        return None
    if is_consumer_domain(domain):
        return await get_or_create_company(session, email.lower(), email)
    return await get_or_create_company(session, domain)
