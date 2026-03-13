from fastapi import APIRouter

from app.schemas.overview import PaperOverviewResponse
from app.services.rag.service import RAGService

router = APIRouter()
rag_service = RAGService()


@router.get("/{paper_id}/overview", response_model=PaperOverviewResponse)
def get_paper_overview(paper_id: str) -> dict:
    return rag_service.get_overview(paper_id)
