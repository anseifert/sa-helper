from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connector: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    records_upserted: int
    error_message: str | None


class SyncResponse(BaseModel):
    status: str
    stages: list[SyncLogOut]


class SyncStatusResponse(BaseModel):
    last_sync_at: datetime | None
    connectors: dict[str, dict]
