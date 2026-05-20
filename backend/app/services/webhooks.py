import json

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting

logger = structlog.get_logger()
WEBHOOK_KEY = "webhook_registrations"


async def register_webhook(session: AsyncSession, url: str, events: list[str]) -> None:
    result = await session.execute(select(Setting).where(Setting.key == WEBHOOK_KEY))
    row = result.scalar_one_or_none()
    regs: list[dict] = []
    if row:
        regs = json.loads(row.value)
    regs.append({"url": url, "events": events})
    if row:
        row.value = json.dumps(regs)
    else:
        session.add(Setting(key=WEBHOOK_KEY, value=json.dumps(regs)))


async def emit_event(session: AsyncSession, event: str, payload: dict) -> None:
    """Stub delivery — logs only; no outbound HTTP in MVP."""
    result = await session.execute(select(Setting).where(Setting.key == WEBHOOK_KEY))
    row = result.scalar_one_or_none()
    if not row:
        return
    regs = json.loads(row.value)
    for reg in regs:
        if event in reg.get("events", []):
            logger.info(
                "webhook_stub_emit",
                event=event,
                url=reg["url"],
                payload=payload,
            )
