from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base
from app.models.company_assets import CompanyAssets

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        db_path = settings.database_url.split("///")[-1]
        if db_path and not db_path.startswith(":"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(settings.database_url, echo=settings.debug)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def _migrate_company_assets(sync_conn) -> None:
    tables = set(inspect(sync_conn).get_table_names())
    if "company_assets" not in tables:
        CompanyAssets.__table__.create(sync_conn)
        return
    existing = {col["name"] for col in inspect(sync_conn).get_columns("company_assets")}
    column_defs = {
        "sub_ocp": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_oke": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_ovm": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_rhel": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_aap": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_acs": "BOOLEAN NOT NULL DEFAULT 0",
        "sub_acm": "BOOLEAN NOT NULL DEFAULT 0",
        "ansible_nodes": "INTEGER NOT NULL DEFAULT 0",
        "rhel_subscriptions": "INTEGER NOT NULL DEFAULT 0",
        "hw_hp": "BOOLEAN NOT NULL DEFAULT 0",
        "hw_dell": "BOOLEAN NOT NULL DEFAULT 0",
        "hw_cisco": "BOOLEAN NOT NULL DEFAULT 0",
        "hw_palo_alto": "BOOLEAN NOT NULL DEFAULT 0",
        "hw_fortinet": "BOOLEAN NOT NULL DEFAULT 0",
        # SQLite ALTER only allows constant defaults; timestamps added nullable then backfilled.
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    }
    for name, typedef in column_defs.items():
        if name not in existing:
            sync_conn.execute(text(f"ALTER TABLE company_assets ADD COLUMN {name} {typedef}"))
    refreshed = {col["name"] for col in inspect(sync_conn).get_columns("company_assets")}
    if "created_at" in refreshed:
        sync_conn.execute(
            text(
                "UPDATE company_assets SET created_at = CURRENT_TIMESTAMP "
                "WHERE created_at IS NULL"
            )
        )
    if "updated_at" in refreshed:
        sync_conn.execute(
            text(
                "UPDATE company_assets SET updated_at = CURRENT_TIMESTAMP "
                "WHERE updated_at IS NULL"
            )
        )


def _migrate_contacts_is_ignored(sync_conn) -> None:
    columns = {col["name"] for col in inspect(sync_conn).get_columns("contacts")}
    if "is_ignored" not in columns:
        sync_conn.execute(
            text(
                "ALTER TABLE contacts ADD COLUMN is_ignored BOOLEAN NOT NULL DEFAULT 0"
            )
        )


async def init_db() -> None:
    from app.services.assets import seed_asset_companies

    engine = get_engine()
    factory = get_session_factory()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_contacts_is_ignored)
        await conn.run_sync(_migrate_company_assets)
    try:
        async with factory() as session:
            await seed_asset_companies(session)
            await session.commit()
    except Exception:
        import structlog

        structlog.get_logger().exception("seed_asset_companies_failed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
