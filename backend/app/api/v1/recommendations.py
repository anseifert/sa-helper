import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationOut
from app.services.recommendation_dismiss import dismiss_recommendation

router = APIRouter()
logger = structlog.get_logger()


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


@router.post("/{rec_id}/dismiss", response_model=RecommendationOut)
async def dismiss_recommendation_endpoint(
    rec_id: int,
    session: AsyncSession = Depends(get_session),
) -> RecommendationOut:
    try:
        return await dismiss_recommendation(session, rec_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("dismiss_recommendation_failed", rec_id=rec_id)
        raise HTTPException(500, f"Could not dismiss item: {e}") from e
