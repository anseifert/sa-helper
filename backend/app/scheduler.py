from apscheduler.schedulers.asyncio import AsyncIOScheduler

import structlog

from app.config import get_settings
from app.db import get_session_factory, init_db
from app.services.sync import run_sync

logger = structlog.get_logger()
scheduler = AsyncIOScheduler()


async def _hourly_sync() -> None:
    logger.info("scheduled_sync_start")
    factory = get_session_factory()
    async with factory() as session:
        try:
            await run_sync(session)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("scheduled_sync_failed")


def start_scheduler() -> None:
    settings = get_settings()
    scheduler.add_job(
        _hourly_sync,
        "interval",
        minutes=settings.sync_interval_minutes,
        id="hourly_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler_started", interval_minutes=settings.sync_interval_minutes)
