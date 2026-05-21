from pydantic import BaseModel

from app.schemas.recommendation import RecommendationOut


class AgingBucket(BaseModel):
    label: str
    count: int


class CompanyTaskCount(BaseModel):
    company_id: int | None
    company_name: str
    count: int


class UntouchedAccount(BaseModel):
    company_id: int
    company_name: str
    last_touch: str | None


class SyncHealthItem(BaseModel):
    connector: str
    status: str
    last_run: str | None
    records_upserted: int
    error_message: str | None


class DashboardOut(BaseModel):
    recommendations: list[RecommendationOut]
    focus_today: list[RecommendationOut]
    open_tasks_by_company: list[CompanyTaskCount]
    aging_buckets: list[AgingBucket]
    untouched_accounts_30d: list[UntouchedAccount]
    sync_health: list[SyncHealthItem]
