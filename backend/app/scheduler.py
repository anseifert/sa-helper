from apscheduler.schedulers.asyncio import AsyncIOScheduler

import structlog

from app.config import get_settings
from app.services.sync_job import run_sync_job

logger = structlog.get_logger()
scheduler = AsyncIOScheduler()


async def _hourly_sync() -> None:
    logger.info("scheduled_sync_start")
    await run_sync_job()


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
