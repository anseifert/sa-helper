from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_session
from app.models.contact import Contact
from app.schemas.contact import ContactOut, ContactUpdate
from app.services.company_service import get_or_create_company
from app.services.ollama import enrich_contact

router = APIRouter()


def _contact_out(c: Contact) -> ContactOut:
    name = None
    if c.company:
        name = c.company.name
    elif c.company_override:
        name = c.company_override
    return ContactOut(
        id=c.id,
        email=c.email,
        display_name=c.display_name,
        company_id=c.company_id,
        company_name=name,
        company_override=c.company_override,
        is_internal=c.is_internal,
        is_ignored=bool(c.is_ignored),
        title=c.title,
        notes=c.notes,
        source=c.source,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    q: str | None = Query(None, description="Search email or name"),
    company_id: int | None = Query(None),
    include_ignored: bool = Query(
        False, description="Include contacts marked as ignored (hidden by default)"
    ),
    session: AsyncSession = Depends(get_session),
) -> list[ContactOut]:
    stmt = select(Contact).options(selectinload(Contact.company))
    if not include_ignored:
        stmt = stmt.where(Contact.is_ignored == False)  # noqa: E712
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(Contact.email.ilike(like), Contact.display_name.ilike(like))
        )
    if company_id is not None:
        stmt = stmt.where(Contact.company_id == company_id)
    stmt = stmt.order_by(Contact.email)
    result = await session.execute(stmt)
    return [_contact_out(c) for c in result.scalars().all()]


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    contact = await session.get(Contact, contact_id, options=[selectinload(Contact.company)])
    if not contact:
        from fastapi import HTTPException

        raise HTTPException(404, "Contact not found")

    if body.company_override is not None:
        contact.company_override = body.company_override
        if body.company_override:
            co = await get_or_create_company(session, body.company_override.lower(), body.company_override)
            contact.company_id = co.id if co else None
    if body.company_id is not None:
        contact.company_id = body.company_id
    if body.is_ignored is not None:
        contact.is_ignored = body.is_ignored

    await session.flush()
    await session.refresh(contact, ["company"])
    return _contact_out(contact)


@router.post("/{contact_id}/enrich", response_model=ContactOut)
async def enrich_contact_endpoint(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
) -> ContactOut:
    contact = await session.get(Contact, contact_id, options=[selectinload(Contact.company)])
    if not contact:
        from fastapi import HTTPException

        raise HTTPException(404, "Contact not found")

    data = await enrich_contact(contact.title or "", contact.email, contact.notes or "")
    if data.get("title"):
        contact.title = data["title"]
    if data.get("notes"):
        contact.notes = data["notes"]
    await session.flush()
    return _contact_out(contact)
