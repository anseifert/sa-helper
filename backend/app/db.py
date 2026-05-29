from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base

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
