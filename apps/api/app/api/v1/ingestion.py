from fastapi import APIRouter

from app.services.ingestion.service import IngestionService

router = APIRouter()
ingestion_service = IngestionService()


@router.get("/jobs/{job_id}")
def get_ingestion_job(job_id: str) -> dict:
    return ingestion_service.get_job(job_id)
