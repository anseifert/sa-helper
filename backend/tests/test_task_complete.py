import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_session
from app.auth import require_auth
from app.main import app
from app.models import Base
from app.models.task import Task
from app.services.task_complete import complete_task


@pytest.mark.asyncio
async def test_complete_task_service():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        session.add(
            Task(
                source="gmail",
                source_id="t:1:user_owes_reply",
                title="Test — reply",
                status="open",
                task_type="user_owes_reply",
                badge_source="gmail",
            )
        )
        await session.commit()

    async with factory() as session:
        out = await complete_task(session, 1)
        assert out.status == "completed"
        await session.commit()


@pytest.mark.asyncio
async def test_complete_task_api():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        session.add(
            Task(
                source="gmail",
                source_id="t:2:user_owes_reply",
                title="API test",
                status="open",
                task_type="user_owes_reply",
                badge_source="gmail",
            )
        )
        await session.commit()

    async def override_session():
        async with factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[require_auth] = lambda: None
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post("/api/v1/tasks/1/complete")
            assert res.status_code == 200
            assert res.json()["status"] == "completed"
    finally:
        app.dependency_overrides.clear()
