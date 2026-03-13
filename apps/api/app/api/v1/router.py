from fastapi import APIRouter

from app.api.v1 import chat, ingestion, memory, overview, papers, recommendations

api_router = APIRouter()
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(overview.router, prefix="/papers", tags=["overview"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(recommendations.router, prefix="/papers", tags=["recommendations"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
