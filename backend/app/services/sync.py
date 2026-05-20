from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.extractors.base import BaseExtractor
from app.extractors.calendar import CalendarExtractor
from app.extractors.drive import DriveExtractor
from app.extractors.gmail import GmailExtractor
from app.extractors.slack import SlackExtractor
from app.models.setting import Setting
from app.models.sync_log import SyncLog
from app.services.google_client import get_google_credentials
from app.services.recommendations import rebuild_recommendations
from app.services.upsert import upsert_contact, upsert_task
from app.services.webhooks import emit_event
from app.utils.domain import email_domain

logger = structlog.get_logger()


async def _log_stage(
    session: AsyncSession,
    connector: str,
    status: str,
    started: datetime,
    count: int = 0,
    error: str | None = None,
) -> SyncLog:
    log = SyncLog(
        connector=connector,
        status=status,
        started_at=started,
        finished_at=datetime.now(timezone.utc),
        records_upserted=count,
        error_message=error,
    )
    session.add(log)
    await session.flush()
    return log


async def _run_extractor_stage(
    session: AsyncSession,
    connector: str,
    extractor: BaseExtractor,
    *,
    contacts: bool,
    user_domain: str,
) -> SyncLog:
    started = datetime.now(timezone.utc)
    count = 0
    try:
        if contacts:
            for c in await extractor.extract_contacts():
                await upsert_contact(session, c, user_domain)
                count += 1
        else:
            for t in await extractor.extract_tasks():
                await upsert_task(session, t, user_domain)
                count += 1
        return await _log_stage(session, connector, "success", started, count)
    except Exception as e:
        logger.exception("sync_stage_failed", connector=connector)
        return await _log_stage(session, connector, "error", started, count, str(e))


async def run_sync(session: AsyncSession) -> list[SyncLog]:
    settings = get_settings()
    logs: list[SyncLog] = []

    creds = await get_google_credentials(session)
    if not creds:
        started = datetime.now(timezone.utc)
        logs.append(
            await _log_stage(
                session, "google", "skipped", started, error="Google not connected"
            )
        )
        return logs

    user_email = settings.user_email
    if not user_email:
        profile = (
            GmailExtractor(creds, "placeholder@local").service.users()
            .getProfile(userId="me")
            .execute()
        )
        user_email = profile.get("emailAddress", "")

    user_domain = email_domain(user_email) or ""
    gmail = GmailExtractor(creds, user_email)

    logs.append(await _run_extractor_stage(session, "gmail_contacts", gmail, contacts=True, user_domain=user_domain))
    logs.append(await _run_extractor_stage(session, "gmail_tasks", gmail, contacts=False, user_domain=user_domain))
    logs.append(
        await _run_extractor_stage(
            session, "calendar", CalendarExtractor(creds, user_email), contacts=False, user_domain=user_domain
        )
    )
    logs.append(
        await _run_extractor_stage(
            session, "drive", DriveExtractor(creds, user_email), contacts=False, user_domain=user_domain
        )
    )
    logs.append(
        await _run_extractor_stage(
            session, "slack", SlackExtractor(), contacts=False, user_domain=user_domain
        )
    )

    started = datetime.now(timezone.utc)
    try:
        await rebuild_recommendations(session)
        logs.append(await _log_stage(session, "recommendations", "success", started, 1))
        await emit_event(session, "recommendations.updated", {})
    except Exception as e:
        logs.append(await _log_stage(session, "recommendations", "error", started, 0, str(e)))

    now_iso = datetime.now(timezone.utc).isoformat()
    setting = await session.get(Setting, "last_sync_at")
    if setting:
        setting.value = now_iso
    else:
        session.add(Setting(key="last_sync_at", value=now_iso))

    await emit_event(session, "sync.completed", {"stages": len(logs)})
    logger.info("sync_completed", stages=len(logs))
    return logs
