from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CatalogItemOut(BaseModel):
    key: str
    label: str


class AssetsCatalogOut(BaseModel):
    subscriptions: list[CatalogItemOut]
    hardware: list[CatalogItemOut]


class AssetCompanyOut(BaseModel):
    company_id: int
    company_name: str
    company_domain: str = ""
    subscriptions: dict[str, bool]
    hardware: dict[str, bool]
    ansible_nodes: int
    rhel_subscriptions: int
    created_at: datetime
    updated_at: datetime


class AvailableCompanyOut(BaseModel):
    id: int
    name: str
    domain: str


class AssetCompanyUpdate(BaseModel):
    company_name: str | None = None
    subscriptions: dict[str, bool] | None = None
    hardware: dict[str, bool] | None = None
    ansible_nodes: int | None = Field(None, ge=0)
    rhel_subscriptions: int | None = Field(None, ge=0)


class AttachAssetCompanyBody(BaseModel):
    company_id: int
