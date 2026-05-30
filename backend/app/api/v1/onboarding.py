import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.models.setting import Setting
from app.schemas.onboarding import OnboardingStatusOut
from app.services.google_client import is_google_connected

router = APIRouter()
logger = structlog.get_logger()

_SETTING_KEYS = {"last_sync_at"}


@router.get("/status", response_model=OnboardingStatusOut)
async def onboarding_status(
    session: AsyncSession = Depends(get_session),
) -> OnboardingStatusOut:
    """Lightweight check for home-page splash; must not raise."""
    try:
        google_connected = await is_google_connected(session)
    except Exception:
        logger.warning("onboarding_google_check_failed", exc_info=True)
        google_connected = False

    last_sync_at: str | None = None
    try:
        result = await session.execute(
            select(Setting).where(Setting.key.in_(_SETTING_KEYS))
        )
        kv = {r.key: r.value for r in result.scalars().all()}
        last_sync_at = kv.get("last_sync_at")
    except Exception:
        logger.warning("onboarding_settings_read_failed", exc_info=True)

    return OnboardingStatusOut(
        google_connected=google_connected,
        last_sync_at=last_sync_at,
        onboarding_complete=bool(google_connected and last_sync_at),
    )
