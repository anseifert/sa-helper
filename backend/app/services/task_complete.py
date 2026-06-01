from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.schemas.task import TaskOut
from app.services.tasks_query import _task_out


async def complete_task(session: AsyncSession, task_id: int) -> TaskOut:
    result = await session.execute(
        select(Task).options(selectinload(Task.company)).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task already completed",
        )
    company_name = task.company.name if task.company else None
    task.status = "completed"
    task.updated_at = datetime.now(timezone.utc)
    await session.flush()
    # flush expires attributes; refresh avoids async lazy-load (MissingGreenlet) on response
    await session.refresh(task)
    return _task_out(task, company_name)
