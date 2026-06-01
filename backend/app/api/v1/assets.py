import structlog
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
logger = structlog.get_logger()


@router.get("/catalog", response_model=AssetsCatalogOut)
async def get_catalog() -> AssetsCatalogOut:
    return assets_catalog()


@router.get("/ready")
async def assets_ready(session: AsyncSession = Depends(get_session)) -> dict:
    """Diagnostics: confirms company_assets table exists (use when debugging 500s)."""
    from sqlalchemy import text

    try:
        count = (
            await session.execute(text("SELECT COUNT(*) FROM company_assets"))
        ).scalar_one()
        return {"ready": True, "company_assets_rows": int(count)}
    except Exception as e:
        logger.exception("assets_ready_check_failed")
        msg = str(e)
        if "no such table" in msg.lower():
            msg = "missing table company_assets — rebuild and restart backend container"
        return {"ready": False, "error": msg}


@router.get("", response_model=list[AssetCompanyOut])
async def get_assets(session: AsyncSession = Depends(get_session)) -> list[AssetCompanyOut]:
    try:
        return await list_asset_companies(session)
    except Exception as e:
        logger.exception("get_assets_failed")
        raise HTTPException(500, f"Could not load assets: {e}") from e


@router.get("/available-companies", response_model=list[AvailableCompanyOut])
async def get_available_companies(
    session: AsyncSession = Depends(get_session),
) -> list[AvailableCompanyOut]:
    try:
        return await list_available_companies(session)
    except Exception as e:
        logger.exception("get_available_companies_failed")
        raise HTTPException(500, f"Could not list companies: {e}") from e


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
    except Exception as e:
        logger.exception("patch_asset_company_failed", company_id=company_id)
        raise HTTPException(500, f"Could not save assets: {e}") from e
