import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.models.setting import Setting

router = APIRouter()

PUBLIC_KEYS = {"last_sync_at", "user_email"}


class SettingsOut(BaseModel):
    google_connected: bool
    slack_configured: bool
    last_sync_at: str | None
    user_email: str | None


@router.get("", response_model=SettingsOut)
async def get_app_settings(session: AsyncSession = Depends(get_session)) -> SettingsOut:
    from app.services.google_client import is_google_connected

    settings = get_settings()
    result = await session.execute(
        select(Setting).where(Setting.key.in_(PUBLIC_KEYS))
    )
    kv = {r.key: r.value for r in result.scalars().all()}
    return SettingsOut(
        google_connected=await is_google_connected(session),
        slack_configured=bool(settings.slack_bot_token),
        last_sync_at=kv.get("last_sync_at"),
        user_email=kv.get("user_email") or settings.user_email or None,
    )
