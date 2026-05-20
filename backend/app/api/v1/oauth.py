from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.schemas.common import MessageResponse
from app.services.oauth_google import google_auth_url, save_google_tokens

router = APIRouter()


@router.get("/google/authorize")
async def google_authorize() -> RedirectResponse:
    return RedirectResponse(google_auth_url())


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    await save_google_tokens(session, code)
    settings = get_settings()
    return RedirectResponse(f"{settings.frontend_url}/settings?connected=google")


@router.get("/google/status", response_model=MessageResponse)
async def google_status(session: AsyncSession = Depends(get_session)) -> MessageResponse:
    from app.services.google_client import is_google_connected

    if await is_google_connected(session):
        return MessageResponse(message="connected")
    return MessageResponse(message="disconnected")
