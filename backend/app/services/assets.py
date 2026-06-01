from datetime import datetime, timezone

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.assets_catalog import (
    ASSET_SEED_COMPANIES,
    HARDWARE_KEYS,
    HARDWARE_PRODUCTS,
    SUBSCRIPTION_KEYS,
    SUBSCRIPTION_PRODUCTS,
)
from app.models.company import Company
from app.models.company_assets import CompanyAssets
from app.schemas.assets import AssetCompanyOut, AssetsCatalogOut, AvailableCompanyOut, CatalogItemOut
from app.services.company_service import get_or_create_company
from app.utils.datetime_util import ensure_utc
from app.utils.priority_accounts import priority_sort_key, tasks_section_id_for_company


def assets_catalog() -> AssetsCatalogOut:
    return AssetsCatalogOut(
        subscriptions=[CatalogItemOut(key=i.key, label=i.label) for i in SUBSCRIPTION_PRODUCTS],
        hardware=[CatalogItemOut(key=i.key, label=i.label) for i in HARDWARE_PRODUCTS],
    )


def _subscriptions_from_row(row: CompanyAssets) -> dict[str, bool]:
    return {key: bool(getattr(row, f"sub_{key}")) for key in SUBSCRIPTION_KEYS}


def _hardware_from_row(row: CompanyAssets) -> dict[str, bool]:
    mapping = {
        "hp": "hw_hp",
        "dell": "hw_dell",
        "cisco": "hw_cisco",
        "palo_alto": "hw_palo_alto",
        "fortinet": "hw_fortinet",
    }
    return {key: bool(getattr(row, mapping[key])) for key in HARDWARE_KEYS}


def _asset_company_out(company: Company, row: CompanyAssets) -> AssetCompanyOut:
    from datetime import datetime, timezone

    created = ensure_utc(row.created_at) or datetime.now(timezone.utc)
    updated = ensure_utc(row.updated_at) or created
    return AssetCompanyOut(
        company_id=company.id,
        company_name=company.name,
        company_domain=company.domain or "",
        subscriptions=_subscriptions_from_row(row),
        hardware=_hardware_from_row(row),
        ansible_nodes=int(row.ansible_nodes or 0),
        rhel_subscriptions=int(row.rhel_subscriptions or 0),
        created_at=created,
        updated_at=updated,
    )


def _sort_companies(companies: list[tuple[Company, CompanyAssets]]) -> list[tuple[Company, CompanyAssets]]:
    def key_fn(pair: tuple[Company, CompanyAssets]) -> tuple[int, str]:
        company, _ = pair
        section = tasks_section_id_for_company(company.name)
        return (priority_sort_key(section), company.name.lower())

    return sorted(companies, key=key_fn)


async def seed_asset_companies(session: AsyncSession) -> None:
    for domain, display_name in ASSET_SEED_COMPANIES:
        company = await get_or_create_company(session, domain, display_name)
        if not company:
            continue
        existing = await session.execute(
            select(CompanyAssets).where(CompanyAssets.company_id == company.id)
        )
        if existing.scalar_one_or_none() is None:
            session.add(CompanyAssets(company_id=company.id))


async def list_asset_companies(session: AsyncSession) -> list[AssetCompanyOut]:
    result = await session.execute(
        select(Company, CompanyAssets).join(
            CompanyAssets, CompanyAssets.company_id == Company.id
        )
    )
    pairs = list(result.all())
    return [_asset_company_out(c, a) for c, a in _sort_companies(pairs)]


async def list_available_companies(session: AsyncSession) -> list[AvailableCompanyOut]:
    result = await session.execute(
        select(Company)
        .where(
            ~exists(
                select(CompanyAssets.id).where(CompanyAssets.company_id == Company.id)
            )
        )
        .order_by(Company.name)
    )
    return [
        AvailableCompanyOut(id=c.id, name=c.name, domain=c.domain)
        for c in result.scalars().all()
    ]


async def attach_company(session: AsyncSession, company_id: int) -> AssetCompanyOut:
    company = await session.get(Company, company_id)
    if not company:
        raise ValueError("Company not found")
    existing = await session.execute(
        select(CompanyAssets).where(CompanyAssets.company_id == company_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Company already on Assets")
    row = CompanyAssets(company_id=company_id)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    await session.refresh(company)
    return _asset_company_out(company, row)


def _apply_subscriptions(row: CompanyAssets, data: dict[str, bool]) -> None:
    for key, value in data.items():
        if key not in SUBSCRIPTION_KEYS:
            continue
        setattr(row, f"sub_{key}", bool(value))


def _apply_hardware(row: CompanyAssets, data: dict[str, bool]) -> None:
    mapping = {
        "hp": "hw_hp",
        "dell": "hw_dell",
        "cisco": "hw_cisco",
        "palo_alto": "hw_palo_alto",
        "fortinet": "hw_fortinet",
    }
    for key, value in data.items():
        col = mapping.get(key)
        if col:
            setattr(row, col, bool(value))


async def update_asset_company(
    session: AsyncSession,
    company_id: int,
    *,
    company_name: str | None = None,
    subscriptions: dict[str, bool] | None = None,
    hardware: dict[str, bool] | None = None,
    ansible_nodes: int | None = None,
    rhel_subscriptions: int | None = None,
) -> AssetCompanyOut:
    company = await session.get(Company, company_id)
    if not company:
        raise ValueError("Company not found")
    result = await session.execute(
        select(CompanyAssets).where(CompanyAssets.company_id == company_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise ValueError("Assets record not found")

    if company_name is not None and company_name.strip():
        company.name = company_name.strip()
    if subscriptions is not None:
        _apply_subscriptions(row, subscriptions)
    if hardware is not None:
        _apply_hardware(row, hardware)
    if ansible_nodes is not None:
        row.ansible_nodes = max(0, int(ansible_nodes))
    if rhel_subscriptions is not None:
        row.rhel_subscriptions = max(0, int(rhel_subscriptions))

    row.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(row)
    await session.refresh(company)
    return _asset_company_out(company, row)
