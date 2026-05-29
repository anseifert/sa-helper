import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.dashboard import DashboardOut
from app.schemas.task_exclusions import TaskExclusionsOut, TaskExclusionsUpdate
from app.services.dashboard import build_dashboard, empty_dashboard
from app.services.task_exclusions import load_task_exclusions, save_task_exclusions

router = APIRouter()
logger = structlog.get_logger()


@router.get("", response_model=DashboardOut)
async def dashboard(session: AsyncSession = Depends(get_session)) -> DashboardOut:
    try:
        return await build_dashboard(session)
    except Exception:
        logger.exception("dashboard_endpoint_failed")
        try:
            exclusions = await load_task_exclusions(session)
        except Exception:
            exclusions = None
        return empty_dashboard(exclusions)


@router.put("/exclusions", response_model=TaskExclusionsOut)
async def update_task_exclusions(
    body: TaskExclusionsUpdate,
    session: AsyncSession = Depends(get_session),
) -> TaskExclusionsOut:
    out = await save_task_exclusions(session, body)
    await session.commit()
    return out
