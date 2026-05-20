from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.common import MessageResponse
from app.schemas.webhook import WebhookRegister
from app.services.webhooks import register_webhook

router = APIRouter()


@router.post("/register", response_model=MessageResponse)
async def register(
    body: WebhookRegister,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    await register_webhook(session, str(body.url), body.events)
    return MessageResponse(message="registered")
