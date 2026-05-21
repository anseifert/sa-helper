from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.utils.datetime_util import ensure_utc
from app.models.company import Company
from app.models.recommendation import Recommendation
from app.models.sync_log import SyncLog
from app.models.task import Task
from app.schemas.dashboard import AgingBucket, DashboardOut, SyncHealthItem
from app.schemas.recommendation import RecommendationOut


async def build_dashboard(session: AsyncSession) -> DashboardOut:
    now = datetime.now(timezone.utc)
    settings = get_settings()
    window_start = now - timedelta(days=settings.task_window_days)

    rec_result = await session.execute(
        select(Recommendation)
        .where(Recommendation.is_active == True, Recommendation.rec_type != "focus_today")
        .order_by(Recommendation.rank_score.desc())
        .limit(15)
    )
    recommendations = [
        RecommendationOut.model_validate(r) for r in rec_result.scalars().all()
    ]

    focus_result = await session.execute(
        select(Recommendation)
        .where(Recommendation.is_active == True, Recommendation.rec_type == "focus_today")
        .order_by(Recommendation.rank_score.desc())
        .limit(5)
    )
    focus = [RecommendationOut.model_validate(r) for r in focus_result.scalars().all()]

    task_result = await session.execute(
        select(Task.company_id, func.count(Task.id))
        .where(Task.status == "open", Task.created_at >= window_start)
        .group_by(Task.company_id)
    )
    company_names: dict[int | None, str] = {}
    c_rows = await session.execute(select(Company))
    for c in c_rows.scalars().all():
        company_names[c.id] = c.name

    open_by_company = [
        {
            "company_id": cid,
            "company_name": company_names.get(cid, "Unassigned"),
            "count": cnt,
        }
        for cid, cnt in task_result.all()
    ]

    open_tasks = await session.execute(
        select(Task).where(Task.status == "open", Task.created_at >= window_start)
    )
    buckets = {"0-7d": 0, "8-14d": 0, "15-30d": 0}
    for t in open_tasks.scalars().all():
        created = ensure_utc(t.created_at)
        if not created:
            continue
        age = (now - created).days
        if age <= 7:
            buckets["0-7d"] += 1
        elif age <= 14:
            buckets["8-14d"] += 1
        else:
            buckets["15-30d"] += 1

    aging = [
        AgingBucket(label=k, count=v) for k, v in buckets.items()
    ]

    untouched: list[dict] = []
    company_last = await session.execute(
        select(
            Company.id,
            Company.name,
            func.max(Task.updated_at).label("last_touch"),
        )
        .join(Task, Task.company_id == Company.id, isouter=True)
        .group_by(Company.id)
    )
    for row in company_last.all():
        last_touch = ensure_utc(row.last_touch)
        if last_touch is None or last_touch < now - timedelta(days=30):
            untouched.append(
                {
                    "company_id": row.id,
                    "company_name": row.name,
                    "last_touch": last_touch.isoformat() if last_touch else None,
                }
            )

    sync_health: list[SyncHealthItem] = []
    for connector in ("gmail_contacts", "gmail_tasks", "calendar", "drive", "slack", "recommendations"):
        log_result = await session.execute(
            select(SyncLog)
            .where(SyncLog.connector == connector)
            .order_by(SyncLog.started_at.desc())
            .limit(1)
        )
        log = log_result.scalar_one_or_none()
        sync_health.append(
            SyncHealthItem(
                connector=connector,
                status=log.status if log else "never",
                last_run=log.finished_at.isoformat() if log and log.finished_at else None,
                records_upserted=log.records_upserted if log else 0,
                error_message=log.error_message if log else None,
            )
        )

    return DashboardOut(
        recommendations=recommendations,
        focus_today=focus,
        open_tasks_by_company=open_by_company,
        aging_buckets=aging,
        untouched_accounts_30d=untouched[:20],
        sync_health=sync_health,
    )
