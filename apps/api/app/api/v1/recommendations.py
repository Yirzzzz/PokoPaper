from fastapi import APIRouter, Query

from app.services.recommendations.service import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


@router.get("/{paper_id}/recommendations")
def get_recommendations(paper_id: str, category: str | None = Query(default=None)) -> dict:
    return recommendation_service.get_recommendations(paper_id=paper_id, category=category)
