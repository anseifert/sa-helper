from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.company import Company
from app.models.task import Task
from app.services.recommendations import rebuild_recommendations


@pytest.mark.asyncio
async def test_rebuild_recommendations_with_naive_task_dates():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        company = Company(name="Acme", domain="acme.com")
        session.add(company)
        await session.flush()
        naive = datetime(2020, 1, 1)
        session.add(
            Task(
                source="gmail",
                source_id="old",
                title="Old task",
                task_type="stale_thread",
                badge_source="gmail",
                company_id=company.id,
                created_at=naive,
                updated_at=naive,
            )
        )
        await session.commit()

    async with factory() as session:
        count = await rebuild_recommendations(session)
        await session.commit()
        assert count >= 0


@pytest.mark.asyncio
async def test_rebuild_recommendations_overdue_aware_due_at():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    aware_due = datetime(2020, 6, 1, tzinfo=timezone.utc)
    async with factory() as session:
        session.add(
            Task(
                source="calendar",
                source_id="due-aware",
                title="Past meeting",
                task_type="schedule_meeting",
                badge_source="calendar",
                due_at=aware_due,
                created_at=datetime(2026, 5, 1),
                updated_at=datetime(2026, 5, 1),
            )
        )
        await session.commit()

    async with factory() as session:
        count = await rebuild_recommendations(session)
        await session.commit()
        assert count >= 1


@pytest.mark.asyncio
async def test_rebuild_recommendations_overdue_naive_due_at():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(
            Task(
                source="calendar",
                source_id="due1",
                title="Past meeting",
                task_type="schedule_meeting",
                badge_source="calendar",
                due_at=datetime(2020, 6, 1),
                created_at=datetime(2026, 5, 1),
                updated_at=datetime(2026, 5, 1),
            )
        )
        await session.commit()

    async with factory() as session:
        count = await rebuild_recommendations(session)
        await session.commit()
        assert count >= 1
