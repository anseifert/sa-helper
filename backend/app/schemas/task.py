from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_id: str
    title: str
    description: str | None
    status: str
    task_type: str
    origin_url: str | None
    badge_source: str
    company_id: int | None
    company_name: str | None = None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_manual: bool


class TaskGroupOut(BaseModel):
    company_key: str
    company_name: str
    company_id: int | None
    tasks: list[TaskOut]
