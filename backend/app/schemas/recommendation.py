from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rec_type: str
    title: str
    body: str | None
    rank_score: float
    company_id: int | None
    task_id: int | None
    contact_id: int | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
