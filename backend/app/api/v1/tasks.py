from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.task import TaskGroupOut
from app.schemas.tasks_summary import TasksSummaryOut
from app.services.tasks_query import list_open_tasks_grouped
from app.services.tasks_summary import build_tasks_summary

router = APIRouter()


@router.get("", response_model=list[TaskGroupOut])
async def list_tasks(session: AsyncSession = Depends(get_session)) -> list[TaskGroupOut]:
    return await list_open_tasks_grouped(session)


@router.get("/summary", response_model=TasksSummaryOut)
async def tasks_summary(session: AsyncSession = Depends(get_session)) -> TasksSummaryOut:
    return await build_tasks_summary(session)
