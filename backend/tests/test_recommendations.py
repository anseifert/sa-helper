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
