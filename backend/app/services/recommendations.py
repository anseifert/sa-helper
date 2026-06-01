import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.recommendation import Recommendation
from app.models.task import Task
from app.services.ollama import polish_recommendation
from app.utils.datetime_util import as_sqlite_utc, sql_utc_days_ago, sql_utc_now
from app.utils.task_filters import CALENDAR_ONLY_TASK_TYPES, CALENDAR_SOURCES

logger = structlog.get_logger()

TYPE_SCORES = {
    "overdue_followup": 100,
    "return_call": 90,
    "send_docs": 85,
    "stale_thread": 80,
    "untouched_account": 75,
    "focus_today": 95,
}


async def rebuild_recommendations(session: AsyncSession) -> int:
    now = sql_utc_now()
    window = sql_utc_days_ago(30)

    await session.execute(update(Recommendation).values(is_active=False))

    recs: list[Recommendation] = []

    overdue = await session.execute(
        select(Task).where(Task.status == "open", Task.due_at.isnot(None))
    )
    for t in overdue.scalars().all():
        due = as_sqlite_utc(t.due_at)
        if due is None or due >= now:
            continue
        recs.append(
            Recommendation(
                rec_type="overdue_followup",
                title=f"Overdue: {t.title[:80]}",
                body=t.description,
                rank_score=TYPE_SCORES["overdue_followup"],
                company_id=t.company_id,
                task_id=t.id,
                is_active=True,
            )
        )

    stale = await session.execute(
        select(Task).where(
            Task.status == "open",
            Task.task_type == "stale_thread",
        )
    )
    for t in stale.scalars().all():
        created = as_sqlite_utc(t.created_at)
        if created is None or created < window:
            continue
        recs.append(
            Recommendation(
                rec_type="stale_thread",
                title=t.title[:120],
                body="Thread stale 7+ days — follow up",
                rank_score=TYPE_SCORES["stale_thread"],
                company_id=t.company_id,
                task_id=t.id,
                is_active=True,
            )
        )

    docs = await session.execute(
        select(Task).where(
            Task.status == "open",
            Task.task_type.in_(["send_docs", "send_data", "drive_mention"]),
        )
    )
    for t in docs.scalars().all():
        recs.append(
            Recommendation(
                rec_type="send_docs",
                title=f"Deliver: {t.title[:80]}",
                body=t.description,
                rank_score=TYPE_SCORES["send_docs"],
                company_id=t.company_id,
                task_id=t.id,
                is_active=True,
            )
        )

    calls = await session.execute(
        select(Task).where(
            Task.status == "open",
            Task.task_type.in_(["schedule_meeting", "return_call"]),
            Task.source.not_in(CALENDAR_SOURCES),
            Task.task_type.not_in(CALENDAR_ONLY_TASK_TYPES),
        )
    )
    for t in calls.scalars().all():
        recs.append(
            Recommendation(
                rec_type="return_call",
                title=t.title[:120],
                body="Schedule or return call",
                rank_score=TYPE_SCORES["return_call"],
                company_id=t.company_id,
                task_id=t.id,
                is_active=True,
            )
        )

    company_last = await session.execute(
        select(
            Company.id,
            Company.name,
            func.max(Task.updated_at).label("last_touch"),
        )
        .join(Task, Task.company_id == Company.id, isouter=True)
        .group_by(Company.id)
    )
    cutoff = window
    for row in company_last.all():
        last = as_sqlite_utc(row.last_touch)
        if last is None or last < cutoff:
            recs.append(
                Recommendation(
                    rec_type="untouched_account",
                    title=f"Account quiet 30+ days: {row.name or 'Unknown'}",
                    body="No recent task activity",
                    rank_score=TYPE_SCORES["untouched_account"],
                    company_id=row.id,
                    is_active=True,
                )
            )

    recs.sort(key=lambda r: r.rank_score, reverse=True)
    top = recs[:15]

    for r in top:
        if r.body:
            try:
                polished = await polish_recommendation(r.title, r.body or "")
                if polished:
                    r.body = polished
            except Exception:
                logger.warning("recommendation_polish_skipped", title=r.title[:80], exc_info=True)
        session.add(r)

    focus = top[:5]
    for r in focus:
        fc = Recommendation(
            rec_type="focus_today",
            title=r.title,
            body=r.body,
            rank_score=TYPE_SCORES["focus_today"],
            company_id=r.company_id,
            task_id=r.task_id,
            contact_id=r.contact_id,
            is_active=True,
        )
        session.add(fc)

    await session.flush()
    logger.info("recommendations_rebuilt", count=len(top))
    return len(top)
