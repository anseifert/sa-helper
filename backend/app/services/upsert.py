import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.extractors.base import ExtractedContact, ExtractedTask
from app.models.contact import Contact
from app.models.task import Task, TaskContact
from app.services.company_service import get_or_create_company, resolve_company_for_email
from app.utils.domain import email_domain


async def upsert_contact(session: AsyncSession, data: ExtractedContact, user_domain: str) -> Contact:
    result = await session.execute(select(Contact).where(Contact.email == data.email.lower()))
    contact = result.scalar_one_or_none()
    domain = email_domain(data.email)
    is_internal = bool(domain and user_domain and domain == user_domain.lower())

    if contact:
        if data.display_name and not contact.display_name:
            contact.display_name = data.display_name
        if data.source_id:
            contact.source_id = data.source_id
        contact.is_internal = is_internal
    else:
        company = None if is_internal else await resolve_company_for_email(session, data.email)
        contact = Contact(
            email=data.email.lower(),
            display_name=data.display_name,
            company_id=company.id if company else None,
            is_internal=is_internal,
            source="gmail",
            source_id=data.source_id,
        )
        session.add(contact)
    await session.flush()
    return contact


async def upsert_task(
    session: AsyncSession, data: ExtractedTask, user_domain: str
) -> Task:
    result = await session.execute(
        select(Task).where(Task.source == data.source, Task.source_id == data.source_id)
    )
    task = result.scalar_one_or_none()

    company = None
    if data.company_domain:
        company = await get_or_create_company(session, data.company_domain.lower())
    elif data.contact_emails:
        for em in data.contact_emails:
            company = await resolve_company_for_email(session, em)
            if company:
                break

    if task:
        task.title = data.title
        task.description = data.description
        task.task_type = data.task_type
        task.origin_url = data.origin_url
        task.badge_source = data.badge_source
        task.due_at = data.due_at
        if task.status != "completed":
            task.status = "open"
        task.company_id = company.id if company else task.company_id
        if data.metadata is not None:
            task.metadata_json = json.dumps(data.metadata)
    else:
        task = Task(
            source=data.source,
            source_id=data.source_id,
            title=data.title,
            description=data.description,
            status="open",
            task_type=data.task_type,
            origin_url=data.origin_url,
            badge_source=data.badge_source,
            company_id=company.id if company else None,
            due_at=data.due_at,
            metadata_json=json.dumps(data.metadata) if data.metadata else None,
        )
        session.add(task)

    await session.flush()

    for em in data.contact_emails:
        c_result = await session.execute(select(Contact).where(Contact.email == em.lower()))
        contact = c_result.scalar_one_or_none()
        if not contact:
            contact = await upsert_contact(
                session,
                ExtractedContact(email=em, source_id=None),
                user_domain,
            )
        link = await session.get(TaskContact, {"task_id": task.id, "contact_id": contact.id})
        if not link:
            session.add(TaskContact(task_id=task.id, contact_id=contact.id))

    await session.flush()
    return task
