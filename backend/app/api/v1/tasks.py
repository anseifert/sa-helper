import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.task import TaskGroupOut, TaskOut
from app.schemas.tasks_summary import TasksSummaryOut
from app.services.task_complete import complete_task
from app.services.tasks_query import list_open_tasks_grouped
from app.services.tasks_summary import build_tasks_summary

router = APIRouter()
logger = structlog.get_logger()


@router.get("", response_model=list[TaskGroupOut])
async def list_tasks(session: AsyncSession = Depends(get_session)) -> list[TaskGroupOut]:
    return await list_open_tasks_grouped(session)


@router.get("/summary", response_model=TasksSummaryOut)
async def tasks_summary(session: AsyncSession = Depends(get_session)) -> TasksSummaryOut:
    return await build_tasks_summary(session)


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task_endpoint(
    task_id: int,
    session: AsyncSession = Depends(get_session),
) -> TaskOut:
    try:
        return await complete_task(session, task_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("complete_task_failed", task_id=task_id)
        raise HTTPException(500, f"Could not complete task: {e}") from e
