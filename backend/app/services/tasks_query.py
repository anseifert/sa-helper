from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.task import Task
from app.schemas.task import TaskGroupOut, TaskOut
from app.utils.priority_accounts import match_priority_account, priority_display_name
from app.utils.task_filters import is_calendar_task


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


async def list_open_tasks(session: AsyncSession) -> list[TaskOut]:
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
    out: list[TaskOut] = []
    for task in sorted(tasks, key=_sort_key):
        if is_calendar_task(
            source=task.source,
            badge_source=task.badge_source,
            task_type=task.task_type,
            title=task.title,
            description=task.description,
            metadata_json=task.metadata_json,
            user_email=settings.user_email,
        ):
            continue
        company = task.company
        cname = company.name if company else None
        out.append(_task_out(task, cname))
    return out


async def list_open_tasks_grouped(session: AsyncSession) -> list[TaskGroupOut]:
    groups: dict[str, TaskGroupOut] = {}
    for task_out in await list_open_tasks(session):
        priority_key = match_priority_account(
            company_name=task_out.company_name,
            title=task_out.title,
            description=task_out.description,
        )
        if priority_key:
            key = priority_key
            name = priority_display_name(priority_key)
        elif task_out.company_name:
            key = task_out.company_name.lower().replace(" ", "_")
            name = task_out.company_name
        else:
            key = "_unassigned"
            name = "Unassigned"

        if key not in groups:
            groups[key] = TaskGroupOut(
                company_key=key,
                company_name=name,
                company_id=task_out.company_id,
                tasks=[],
            )
        groups[key].tasks.append(task_out)

    return sorted(groups.values(), key=lambda g: g.company_name.lower())
