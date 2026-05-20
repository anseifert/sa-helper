from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.task import TaskGroupOut
from app.services.tasks_query import list_open_tasks_grouped

router = APIRouter()


@router.get("", response_model=list[TaskGroupOut])
async def list_tasks(session: AsyncSession = Depends(get_session)) -> list[TaskGroupOut]:
    return await list_open_tasks_grouped(session)
