from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.assets import (
    AssetCompanyOut,
    AssetCompanyUpdate,
    AssetsCatalogOut,
    AttachAssetCompanyBody,
    AvailableCompanyOut,
)
from app.services.assets import (
    assets_catalog,
    attach_company,
    list_asset_companies,
    list_available_companies,
    update_asset_company,
)

router = APIRouter()


@router.get("/catalog", response_model=AssetsCatalogOut)
async def get_catalog() -> AssetsCatalogOut:
    return assets_catalog()


@router.get("", response_model=list[AssetCompanyOut])
async def get_assets(session: AsyncSession = Depends(get_session)) -> list[AssetCompanyOut]:
    return await list_asset_companies(session)


@router.get("/available-companies", response_model=list[AvailableCompanyOut])
async def get_available_companies(
    session: AsyncSession = Depends(get_session),
) -> list[AvailableCompanyOut]:
    return await list_available_companies(session)


@router.post("/companies", response_model=AssetCompanyOut, status_code=201)
async def add_asset_company(
    body: AttachAssetCompanyBody,
    session: AsyncSession = Depends(get_session),
) -> AssetCompanyOut:
    try:
        return await attach_company(session, body.company_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.patch("/companies/{company_id}", response_model=AssetCompanyOut)
async def patch_asset_company(
    company_id: int,
    body: AssetCompanyUpdate,
    session: AsyncSession = Depends(get_session),
) -> AssetCompanyOut:
    try:
        return await update_asset_company(
            session,
            company_id,
            company_name=body.company_name,
            subscriptions=body.subscriptions,
            hardware=body.hardware,
            ansible_nodes=body.ansible_nodes,
            rhel_subscriptions=body.rhel_subscriptions,
        )
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
