from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.dashboard import DashboardOut
from app.services.dashboard import build_dashboard

router = APIRouter()


@router.get("", response_model=DashboardOut)
async def dashboard(session: AsyncSession = Depends(get_session)) -> DashboardOut:
    return await build_dashboard(session)
