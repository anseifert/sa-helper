from pydantic import BaseModel

from app.schemas.recommendation import RecommendationOut
from app.schemas.task_exclusions import TaskExclusionsOut


class AgingBucket(BaseModel):
    label: str
    count: int


class CompanyTaskCount(BaseModel):
    company_id: int | None
    company_name: str
    section_id: str
    count: int


class UntouchedAccount(BaseModel):
    company_id: int
    company_name: str
    last_touch: str | None


class TodayMeetingOut(BaseModel):
    event_id: str
    title: str
    start_at: str
    end_at: str | None
    external_emails: list[str]
    html_link: str | None


class SyncHealthItem(BaseModel):
    connector: str
    status: str
    last_run: str | None
    records_upserted: int
    error_message: str | None


class TodayMeetingsOut(BaseModel):
    meetings: list[TodayMeetingOut]
    error: str | None = None


class DashboardOut(BaseModel):
    recommendations: list[RecommendationOut]
    focus_today: list[RecommendationOut]
    today_meetings: list[TodayMeetingOut]
    today_meetings_error: str | None = None
    open_tasks_by_company: list[CompanyTaskCount]
    aging_buckets: list[AgingBucket]
    untouched_accounts_30d: list[UntouchedAccount]
    sync_health: list[SyncHealthItem]
    task_exclusions: TaskExclusionsOut
