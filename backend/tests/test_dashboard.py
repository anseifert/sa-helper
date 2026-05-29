from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.company import Company
from app.models.recommendation import Recommendation
from app.models.task import Task
from app.services.dashboard import build_dashboard


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        company = Company(name="Exxon", domain="exxon.com")
        sess.add(company)
        await sess.flush()
        # Naive datetimes (common in SQLite) — previously caused TypeError on age math.
        naive = datetime(2026, 5, 10)
        sess.add(
            Task(
                source="gmail",
                source_id="t1",
                title="Follow up",
                task_type="user_owes_reply",
                badge_source="gmail",
                company_id=company.id,
                created_at=naive,
                updated_at=naive,
            )
        )
        sess.add(
            Recommendation(
                rec_type="stale_thread",
                title="Stale",
                rank_score=80.0,
                is_active=True,
                created_at=naive,
                updated_at=naive,
            )
        )
        await sess.commit()
        yield sess


@pytest.mark.asyncio
async def test_build_dashboard_with_naive_datetimes(session: AsyncSession):
    result = await build_dashboard(session)
    assert sum(b.count for b in result.aging_buckets) >= 1
    assert len(result.recommendations) == 1
    assert result.open_tasks_by_company[0].company_name == "Exxon"
    assert result.open_tasks_by_company[0].section_id == "exxonmobil"
    assert result.task_exclusions.emails == []
    assert result.today_meetings == []
