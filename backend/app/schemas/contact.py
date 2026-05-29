from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    company_id: int | None
    company_name: str | None = None
    company_override: str | None
    is_internal: bool
    is_ignored: bool = False
    title: str | None
    notes: str | None
    source: str
    created_at: datetime
    updated_at: datetime


class ContactUpdate(BaseModel):
    company_override: str | None = None
    company_id: int | None = None
    is_ignored: bool | None = None
