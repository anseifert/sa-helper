import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base
from app.models.company import Company
from app.services.assets import (
    attach_company,
    list_asset_companies,
    list_available_companies,
    seed_asset_companies,
    update_asset_company,
)


@pytest.mark.asyncio
async def test_assets_seed_and_update():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        session.add(Company(name="Acme Corp", domain="acme.com"))
        await session.commit()

    async with factory() as session:
        await seed_asset_companies(session)
        await session.commit()

    async with factory() as session:
        listed = await list_asset_companies(session)
        assert len(listed) == 4
        names = {c.company_name for c in listed}
        assert "ExxonMobil" in names
        assert "Windstream / Uniti" in names

    async with factory() as session:
        avail = await list_available_companies(session)
        assert len(avail) == 1
        assert avail[0].name == "Acme Corp"
        row = await attach_company(session, avail[0].id)
        await session.commit()
        assert row.ansible_nodes == 0

    async with factory() as session:
        updated = await update_asset_company(
            session,
            row.company_id,
            subscriptions={"ocp": True, "rhel": True},
            hardware={"hp": True, "cisco": True},
            ansible_nodes=5,
            rhel_subscriptions=12,
        )
        await session.commit()
        assert updated.subscriptions["ocp"] is True
        assert updated.hardware["fortinet"] is False
        assert updated.ansible_nodes == 5
