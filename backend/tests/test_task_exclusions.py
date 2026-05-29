from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.models import Base
from app.models.company import Company
from app.models.contact import Contact
from app.models.task import Task, TaskContact
from app.schemas.task_exclusions import TaskExclusionsOut, TaskExclusionsUpdate
from app.services.dashboard import build_dashboard
from app.services.task_exclusions import (
    normalize_company_target,
    normalize_email,
    save_task_exclusions,
    task_matches_exclusion,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("User@Example.COM", "user@example.com"),
        ("bad", None),
    ],
)
def test_normalize_email(raw, expected):
    assert normalize_email(raw) == expected


def test_normalize_company_target():
    assert normalize_company_target("Acme Corp") == "acme corp"
    assert normalize_company_target("acme.com") == "acme.com"
    assert normalize_company_target("bob@acme.com") == "acme.com"


@pytest.mark.asyncio
async def test_exclude_by_email_and_company():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        company = Company(name="Vendor Inc", domain="vendor.com")
        session.add(company)
        await session.flush()
        contact = Contact(email="noise@vendor.com", source="gmail")
        session.add(contact)
        await session.flush()

        naive = datetime(2026, 5, 10)
        keep = Task(
            source="gmail",
            source_id="keep",
            title="Real work",
            task_type="user_owes_reply",
            badge_source="gmail",
            company_id=company.id,
            created_at=naive,
            updated_at=naive,
        )
        drop_email = Task(
            source="gmail",
            source_id="drop-email",
            title="Newsletter",
            task_type="user_owes_reply",
            badge_source="gmail",
            created_at=naive,
            updated_at=naive,
        )
        session.add_all([keep, drop_email])
        await session.flush()
        session.add(TaskContact(task_id=drop_email.id, contact_id=contact.id))
        await session.commit()

    async def _load_task(session, task_id: int) -> Task:
        result = await session.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.company),
                selectinload(Task.contacts).selectinload(TaskContact.contact),
            )
        )
        return result.scalar_one()

    async with factory() as session:
        rules = TaskExclusionsOut(emails=["noise@vendor.com"])
        assert task_matches_exclusion(await _load_task(session, drop_email.id), rules)
        assert not task_matches_exclusion(await _load_task(session, keep.id), rules)

    async with factory() as session:
        await save_task_exclusions(
            session, TaskExclusionsUpdate(emails=["noise@vendor.com"], companies=[])
        )
        await session.commit()
        dash = await build_dashboard(session)
        assert dash.open_tasks_by_company[0].count == 1
        assert dash.aging_buckets[0].count + dash.aging_buckets[1].count + dash.aging_buckets[2].count == 1
