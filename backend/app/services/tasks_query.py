from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.company import Company
from app.models.task import Task
from app.schemas.task import TaskGroupOut, TaskOut


def _sort_key(task: Task) -> datetime:
    return task.created_at or task.due_at or datetime.min.replace(tzinfo=timezone.utc)


def _task_out(task: Task, company_name: str | None) -> TaskOut:
    return TaskOut(
        id=task.id,
        source=task.source,
        source_id=task.source_id,
        title=task.title,
        description=task.description,
        status=task.status,
        task_type=task.task_type,
        origin_url=task.origin_url,
        badge_source=task.badge_source,
        company_id=task.company_id,
        company_name=company_name,
        due_at=task.due_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        is_manual=task.is_manual,
    )


async def list_open_tasks_grouped(session: AsyncSession) -> list[TaskGroupOut]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=settings.task_window_days)
    window_end = now + timedelta(days=settings.task_window_days)

    result = await session.execute(
        select(Task)
        .options(selectinload(Task.company))
        .where(
            Task.status == "open",
            Task.created_at >= window_start,
            or_(Task.due_at.is_(None), Task.due_at <= window_end),
        )
    )
    tasks = list(result.scalars().all())

    groups: dict[str, TaskGroupOut] = {}
    for task in sorted(tasks, key=_sort_key):
        company = task.company
        if company:
            key = company.domain
            name = company.name
            cid = company.id
        else:
            key = "_unassigned"
            name = "Unassigned"
            cid = None

        if key not in groups:
            groups[key] = TaskGroupOut(
                company_key=key,
                company_name=name,
                company_id=cid,
                tasks=[],
            )
        cname = company.name if company else None
        groups[key].tasks.append(_task_out(task, cname))

    return sorted(groups.values(), key=lambda g: g.company_name.lower())
