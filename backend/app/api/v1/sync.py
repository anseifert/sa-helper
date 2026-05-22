from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.setting import Setting
from app.models.sync_log import SyncLog
from app.schemas.sync import SyncLogOut, SyncStartResponse, SyncStatusResponse
from app.services.sync_job import run_sync_job, sync_in_progress

router = APIRouter()

_CONNECTORS = (
    "gmail_contacts",
    "gmail_tasks",
    "calendar",
    "drive",
    "slack",
    "recommendations",
)


@router.post("", response_model=SyncStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(background_tasks: BackgroundTasks) -> SyncStartResponse:
    if sync_in_progress():
        return SyncStartResponse(status="already_running", message="Sync is already in progress.")
    background_tasks.add_task(run_sync_job)
    return SyncStartResponse(
        status="started",
        message="Sync started. Poll GET /api/v1/sync/status until in_progress is false.",
    )


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
    setting = await session.get(Setting, "last_sync_at")
    last = datetime.fromisoformat(setting.value) if setting else None

    connectors: dict[str, dict] = {}
    for name in _CONNECTORS:
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

    return SyncStatusResponse(
        last_sync_at=last,
        in_progress=sync_in_progress(),
        connectors=connectors,
    )
