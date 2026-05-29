import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.schemas.common import HealthResponse
from app.services.google_client import is_google_connected
from app.services.ollama import check_ollama_health

router = APIRouter()
logger = structlog.get_logger()

# Bump when verifying production deploy (curl /api/v1/health).
APP_VERSION = "2026.05.22-calendar-today-tz"


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    settings = get_settings()
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    google_connected = False
    try:
        google_connected = await is_google_connected(session)
    except Exception:
        logger.warning("health_google_check_failed", exc_info=True)

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        ollama=await check_ollama_health(),
        google_connected=google_connected,
        app_version=APP_VERSION,
        auth_enabled=bool(settings.app_password),
    )
