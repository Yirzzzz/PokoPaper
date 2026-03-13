from fastapi import APIRouter, File, Response, UploadFile

from app.schemas.papers import (
    PaperCard,
    PaperStructureResponse,
    UpdatePaperRequest,
    UploadPaperResponse,
)
from app.services.ingestion.service import IngestionService
from app.services.papers.service import PaperService

router = APIRouter()
paper_service = PaperService()
ingestion_service = IngestionService()


@router.get("", response_model=list[PaperCard])
def list_papers() -> list[dict]:
    return paper_service.list_papers()


@router.post("/upload", response_model=UploadPaperResponse)
async def upload_paper(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    return await ingestion_service.upload_and_process(filename=file.filename or "paper.pdf", content=content)


@router.get("/{paper_id}")
def get_paper(paper_id: str) -> dict:
    return paper_service.get_paper(paper_id)


@router.get("/{paper_id}/structure", response_model=PaperStructureResponse)
def get_paper_structure(paper_id: str) -> dict:
    return paper_service.get_structure(paper_id)


@router.patch("/{paper_id}", response_model=PaperCard)
def update_paper(paper_id: str, payload: UpdatePaperRequest) -> dict:
    return paper_service.update_paper(
        paper_id=paper_id,
        category=payload.category,
        tags=payload.tags,
    )


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str) -> Response:
    paper_service.delete_paper(paper_id)
    return Response(status_code=204)
