from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.common import HealthResponse
from app.services.google_client import is_google_connected
from app.services.ollama import check_ollama_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        ollama=await check_ollama_health(),
        google_connected=await is_google_connected(session),
    )
