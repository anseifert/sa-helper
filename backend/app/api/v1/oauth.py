import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.schemas.common import MessageResponse
from app.services.oauth_google import google_auth_url, public_callback_url, save_google_tokens

router = APIRouter()
logger = structlog.get_logger()


def _settings_redirect(query: str) -> RedirectResponse:
    settings = get_settings()
    base = settings.frontend_url.rstrip("/")
    return RedirectResponse(f"{base}/settings?{query}")


@router.get("/google/authorize")
async def google_authorize() -> RedirectResponse:
    return RedirectResponse(google_auth_url())


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if request.query_params.get("error"):
        await session.rollback()
        logger.warning(
            "google_oauth_denied",
            error=request.query_params.get("error"),
            description=request.query_params.get("error_description"),
        )
        return _settings_redirect("oauth_error=google")

    if not request.query_params.get("code"):
        await session.rollback()
        logger.warning("google_oauth_missing_code")
        return _settings_redirect("oauth_error=google")

    try:
        await save_google_tokens(session, public_callback_url(request))
    except Exception:
        await session.rollback()
        logger.exception(
            "google_oauth_callback_failed",
            callback_url=public_callback_url(request).split("code=")[0] + "code=…",
        )
        return _settings_redirect("oauth_error=google")

    return _settings_redirect("connected=google")


@router.get("/google/status", response_model=MessageResponse)
async def google_status(session: AsyncSession = Depends(get_session)) -> MessageResponse:
    from app.services.google_client import is_google_connected

    if await is_google_connected(session):
        return MessageResponse(message="connected")
    return MessageResponse(message="disconnected")
