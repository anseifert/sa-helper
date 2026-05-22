import asyncio

import structlog

from app.db import get_session_factory
from app.services.sync import run_sync

logger = structlog.get_logger()

_lock = asyncio.Lock()
_running = False


def sync_in_progress() -> bool:
    return _running


async def run_sync_job() -> None:
    """Run a full sync in the background with its own DB session."""
    global _running
    async with _lock:
        if _running:
            logger.info("sync_job_skipped_already_running")
            return
        _running = True

    try:
        logger.info("sync_job_started")
        factory = get_session_factory()
        async with factory() as session:
            try:
                await run_sync(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        logger.info("sync_job_finished")
    except Exception:
        logger.exception("sync_job_failed")
    finally:
        _running = False
