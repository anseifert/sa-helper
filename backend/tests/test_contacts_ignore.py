import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base
from app.models.contact import Contact


@pytest.mark.asyncio
async def test_contact_is_ignored_column():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(Contact(email="noise@example.com", source="gmail", is_ignored=True))
        session.add(Contact(email="keep@example.com", source="gmail"))
        await session.commit()

    async with factory() as session:
        visible = (
            await session.execute(select(Contact).where(Contact.is_ignored == False))  # noqa: E712
        ).scalars().all()
        assert len(visible) == 1
        assert visible[0].email == "keep@example.com"
