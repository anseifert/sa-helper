from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str
    created_at: datetime
    updated_at: datetime


class CompanyUpdate(BaseModel):
    name: str | None = None
