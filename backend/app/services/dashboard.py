import math
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.company import Company
from app.models.recommendation import Recommendation
from app.models.sync_log import SyncLog
from app.models.task import Task, TaskContact
from app.services.calendar_today import fetch_today_external_meetings
from app.services.task_exclusions import load_task_exclusions, task_matches_exclusion
from app.schemas.dashboard import (
    AgingBucket,
    CompanyTaskCount,
    DashboardOut,
    SyncHealthItem,
    TodayMeetingOut,
    UntouchedAccount,
)
from app.schemas.task_exclusions import TaskExclusionsOut
from app.schemas.recommendation import RecommendationOut
from app.utils.datetime_util import ensure_utc, sql_utc_days_ago
from app.utils.priority_accounts import tasks_section_id_for_company
from app.utils.task_filters import is_calendar_task

logger = structlog.get_logger()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sql_cutoff(days: int) -> datetime:
    """Naive UTC for SQLite comparisons (avoids aware/naive errors)."""
    return (_utc_now() - timedelta(days=days)).replace(tzinfo=None)


def _safe_rank_score(value: float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0.0
    return float(value)


def _recommendation_out(row: Recommendation) -> RecommendationOut:
    created = ensure_utc(row.created_at) or _utc_now()
    return RecommendationOut(
        id=row.id,
        rec_type=row.rec_type or "unknown",
        title=(row.title or "Untitled")[:512],
        body=row.body,
        rank_score=_safe_rank_score(row.rank_score),
        company_id=row.company_id,
        task_id=row.task_id,
        contact_id=row.contact_id,
        expires_at=ensure_utc(row.expires_at),
        is_active=bool(row.is_active),
        created_at=created,
    )


def _iso_or_none(dt: datetime | None) -> str | None:
    normalized = ensure_utc(dt)
    return normalized.isoformat() if normalized else None


async def _open_tasks_in_window(session: AsyncSession, window_start) -> list[Task]:
    result = await session.execute(
        select(Task)
        .options(
            selectinload(Task.company),
            selectinload(Task.contacts).selectinload(TaskContact.contact),
        )
        .where(Task.status == "open", Task.created_at >= window_start)
    )
    return list(result.scalars().all())


def empty_dashboard(exclusions: TaskExclusionsOut | None = None) -> DashboardOut:
    return DashboardOut(
        recommendations=[],
        focus_today=[],
        today_meetings=[],
        today_meetings_error=None,
        open_tasks_by_company=[],
        aging_buckets=[
            AgingBucket(label="0-7d", count=0),
            AgingBucket(label="8-14d", count=0),
            AgingBucket(label="15-30d", count=0),
        ],
        untouched_accounts_30d=[],
        sync_health=[],
        task_exclusions=exclusions or TaskExclusionsOut(),
    )


async def build_dashboard(session: AsyncSession) -> DashboardOut:
    now = _utc_now()
    settings = get_settings()
    window_start = _sql_cutoff(settings.task_window_days)
    exclusions = await load_task_exclusions(session)

    today_meetings: list[TodayMeetingOut] = []
    today_meetings_error: str | None = None
    today_meetings, today_meetings_error = await fetch_today_external_meetings(session)

    recommendations: list[RecommendationOut] = []
    focus: list[RecommendationOut] = []

    try:
        rec_result = await session.execute(
            select(Recommendation)
            .where(Recommendation.is_active == True, Recommendation.rec_type != "focus_today")
            .order_by(Recommendation.rank_score.desc())
            .limit(15)
        )
        for row in rec_result.scalars().all():
            try:
                recommendations.append(_recommendation_out(row))
            except Exception:
                logger.warning("dashboard_skip_recommendation", rec_id=row.id, exc_info=True)

        focus_result = await session.execute(
            select(Recommendation)
            .where(Recommendation.is_active == True, Recommendation.rec_type == "focus_today")
            .order_by(Recommendation.rank_score.desc())
            .limit(5)
        )
        for row in focus_result.scalars().all():
            try:
                focus.append(_recommendation_out(row))
            except Exception:
                logger.warning("dashboard_skip_focus", rec_id=row.id, exc_info=True)
    except Exception:
        logger.exception("dashboard_recommendations_failed")

    company_names: dict[int | None, str] = {}
    try:
        c_rows = await session.execute(select(Company))
        for c in c_rows.scalars().all():
            company_names[c.id] = c.name
    except Exception:
        logger.exception("dashboard_companies_failed")

    open_by_company: list[CompanyTaskCount] = []
    aging = [
        AgingBucket(label="0-7d", count=0),
        AgingBucket(label="8-14d", count=0),
        AgingBucket(label="15-30d", count=0),
    ]
    bucket_map = {b.label: b for b in aging}

    try:
        counts_by_company: dict[int | None, int] = {}
        for t in await _open_tasks_in_window(session, window_start):
            if is_calendar_task(
                source=t.source,
                badge_source=t.badge_source,
                task_type=t.task_type,
                title=t.title,
                description=t.description,
                metadata_json=t.metadata_json,
                user_email=settings.user_email,
            ):
                continue
            if task_matches_exclusion(t, exclusions):
                continue
            cid = t.company_id
            counts_by_company[cid] = counts_by_company.get(cid, 0) + 1
            created = ensure_utc(t.created_at)
            if not created:
                continue
            age = (now - created).days
            if age <= 7:
                bucket_map["0-7d"].count += 1
            elif age <= 14:
                bucket_map["8-14d"].count += 1
            else:
                bucket_map["15-30d"].count += 1

        open_by_company = []
        for cid, cnt in sorted(
            counts_by_company.items(),
            key=lambda item: company_names.get(item[0], "Unassigned").lower(),
        ):
            name = company_names.get(cid, "Unassigned")
            open_by_company.append(
                CompanyTaskCount(
                    company_id=cid,
                    company_name=name,
                    section_id=tasks_section_id_for_company(name),
                    count=cnt,
                )
            )
    except Exception:
        logger.exception("dashboard_tasks_failed")

    untouched: list[UntouchedAccount] = []
    try:
        company_last = await session.execute(
            select(
                Company.id,
                Company.name,
                func.max(Task.updated_at).label("last_touch"),
            )
            .join(Task, Task.company_id == Company.id, isouter=True)
            .group_by(Company.id)
        )
        cutoff = sql_utc_days_ago(30)
        for row in company_last.all():
            last_touch = row.last_touch
            if last_touch is not None and last_touch.tzinfo is not None:
                last_touch = last_touch.replace(tzinfo=None)
            if last_touch is None or last_touch < cutoff:
                untouched.append(
                    UntouchedAccount(
                        company_id=row.id,
                        company_name=row.name,
                        last_touch=_iso_or_none(row.last_touch),
                    )
                )
    except Exception:
        logger.exception("dashboard_untouched_failed")

    sync_health: list[SyncHealthItem] = []
    for connector in (
        "gmail_contacts",
        "gmail_tasks",
        "calendar",
        "drive",
        "slack",
        "recommendations",
    ):
        try:
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
                    status=(log.status if log else None) or "never",
                    last_run=_iso_or_none(log.finished_at) if log else None,
                    records_upserted=int(log.records_upserted) if log else 0,
                    error_message=log.error_message if log else None,
                )
            )
        except Exception:
            logger.warning("dashboard_sync_health_failed", connector=connector, exc_info=True)
            sync_health.append(
                SyncHealthItem(
                    connector=connector,
                    status="never",
                    last_run=None,
                    records_upserted=0,
                    error_message=None,
                )
            )

    return DashboardOut(
        recommendations=recommendations,
        focus_today=focus,
        today_meetings=today_meetings,
        today_meetings_error=today_meetings_error,
        open_tasks_by_company=open_by_company,
        aging_buckets=aging,
        untouched_accounts_30d=untouched[:20],
        sync_health=sync_health,
        task_exclusions=exclusions,
    )
