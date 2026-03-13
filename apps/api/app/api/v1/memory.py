from fastapi import APIRouter

from app.schemas.memory import MemoryOverviewResponse, ReadingMemoryResponse
from app.services.memory.service import MemoryService

router = APIRouter()
memory_service = MemoryService()


@router.get("/overview", response_model=MemoryOverviewResponse)
def get_memory_overview() -> dict:
    return memory_service.get_overview()


@router.get("/papers/{paper_id}", response_model=ReadingMemoryResponse)
def get_paper_memory(paper_id: str) -> dict:
    return memory_service.get_paper_memory(paper_id)
