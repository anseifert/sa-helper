from pydantic import BaseModel

from app.schemas.recommendation import RecommendationOut
from app.schemas.task import TaskGroupOut


class AgingBucket(BaseModel):
    label: str
    count: int


class SyncHealthItem(BaseModel):
    connector: str
    status: str
    last_run: str | None
    records_upserted: int
    error_message: str | None


class DashboardOut(BaseModel):
    recommendations: list[RecommendationOut]
    focus_today: list[RecommendationOut]
    open_tasks_by_company: list[dict]
    aging_buckets: list[AgingBucket]
    untouched_accounts_30d: list[dict]
    sync_health: list[SyncHealthItem]
