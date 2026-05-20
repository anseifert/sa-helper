from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.company import Company
from app.schemas.company import CompanyOut, CompanyUpdate

router = APIRouter()


@router.get("", response_model=list[CompanyOut])
async def list_companies(session: AsyncSession = Depends(get_session)) -> list[CompanyOut]:
    result = await session.execute(select(Company).order_by(Company.name))
    return [CompanyOut.model_validate(c) for c in result.scalars().all()]


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: int,
    body: CompanyUpdate,
    session: AsyncSession = Depends(get_session),
) -> CompanyOut:
    company = await session.get(Company, company_id)
    if not company:
        raise HTTPException(404, "Company not found")
    if body.name is not None:
        company.name = body.name
    await session.flush()
    return CompanyOut.model_validate(company)
