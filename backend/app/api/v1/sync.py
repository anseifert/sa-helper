from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.setting import Setting
from app.models.sync_log import SyncLog
from app.schemas.sync import SyncLogOut, SyncResponse, SyncStatusResponse
from app.services.sync import run_sync

router = APIRouter()


@router.post("", response_model=SyncResponse)
async def trigger_sync(session: AsyncSession = Depends(get_session)) -> SyncResponse:
    logs = await run_sync(session)
    return SyncResponse(status="completed", stages=[SyncLogOut.model_validate(l) for l in logs])


@router.get("/logs", response_model=list[SyncLogOut])
async def sync_logs(
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[SyncLogOut]:
    result = await session.execute(
        select(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit)
    )
    return [SyncLogOut.model_validate(l) for l in result.scalars().all()]


@router.get("/status", response_model=SyncStatusResponse)
async def sync_status(session: AsyncSession = Depends(get_session)) -> SyncStatusResponse:
    from datetime import datetime

    setting = await session.get(Setting, "last_sync_at")
    last = datetime.fromisoformat(setting.value) if setting else None

    connectors: dict[str, dict] = {}
    for name in ("gmail_contacts", "gmail_tasks", "calendar", "drive", "slack"):
        result = await session.execute(
            select(SyncLog)
            .where(SyncLog.connector == name)
            .order_by(SyncLog.started_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        connectors[name] = {
            "status": log.status if log else "never",
            "records_upserted": log.records_upserted if log else 0,
            "error": log.error_message if log else None,
        }

    return SyncStatusResponse(last_sync_at=last, connectors=connectors)
