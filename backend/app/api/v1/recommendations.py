from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationOut

router = APIRouter()


@router.get("", response_model=list[RecommendationOut])
async def list_recommendations(
    limit: int = Query(15, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[RecommendationOut]:
    result = await session.execute(
        select(Recommendation)
        .where(Recommendation.is_active == True)
        .order_by(Recommendation.rank_score.desc())
        .limit(limit)
    )
    return [RecommendationOut.model_validate(r) for r in result.scalars().all()]
