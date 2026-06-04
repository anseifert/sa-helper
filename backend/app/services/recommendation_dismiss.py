from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationOut


async def dismiss_recommendation(session: AsyncSession, rec_id: int) -> RecommendationOut:
    rec = await session.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    if not rec.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recommendation already dismissed",
        )
    rec.is_active = False
    rec.updated_at = datetime.now(timezone.utc)
    await session.flush()
    await session.refresh(rec)
    return RecommendationOut.model_validate(rec)
