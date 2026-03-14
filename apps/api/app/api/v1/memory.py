from fastapi import APIRouter, HTTPException, Query

from app.schemas.memory import (
    MemoryItem,
    MemoryItemListResponse,
    MemoryOverviewResponse,
    PaperEntityMemoryCard,
    PaperEntityMemoryListResponse,
    MemoryResetRequest,
    ReadingMemoryResponse,
    SessionMemoryListResponse,
    SessionSummaryListResponse,
    SessionSummaryView,
    SessionMemoryView,
    UserMemoryResponse,
)
from app.services.memory.service import MemoryService
from app.services.paper_entity_memory import PaperEntityMemoryService
from app.services.short_term_memory import ShortTermMemoryService

router = APIRouter()
memory_service = MemoryService()
short_term_memory_service = ShortTermMemoryService()
paper_entity_memory_service = PaperEntityMemoryService()


@router.get("/overview", response_model=MemoryOverviewResponse)
def get_memory_overview() -> dict:
    return memory_service.get_overview()


@router.get("/papers/{paper_id}", response_model=ReadingMemoryResponse)
def get_paper_memory(paper_id: str) -> dict:
    return memory_service.get_paper_memory(paper_id)


@router.get("/paper-entities", response_model=PaperEntityMemoryListResponse)
def list_paper_entity_memories() -> dict:
    items = paper_entity_memory_service.list_cards()
    return {"items": items, "total": len(items)}


@router.get("/paper-entities/{paper_id}", response_model=PaperEntityMemoryCard)
def get_paper_entity_memory(paper_id: str) -> dict:
    try:
        return paper_entity_memory_service.get_card(paper_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/user", response_model=UserMemoryResponse)
def get_user_memory() -> dict:
    return memory_service.get_user_memory()


@router.get("/items", response_model=MemoryItemListResponse)
def list_memory_items(
    scope: str | None = Query(default=None),
    paper_id: str | None = Query(default=None),
    memory_type: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
) -> dict:
    items = memory_service.list_memory_items(
        scope=scope,
        paper_id=paper_id,
        memory_type=memory_type,
        enabled=enabled,
    )
    return {"items": items, "total": len(items)}


@router.get("/items/{memory_id}", response_model=MemoryItem)
def get_memory_item(memory_id: str) -> dict:
    try:
        return memory_service.get_memory_item(memory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/items/{memory_id}")
def delete_memory_item(memory_id: str) -> dict:
    try:
        memory_service.delete_memory_item(memory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/items/{memory_id}/disable", response_model=MemoryItem)
def disable_memory_item(memory_id: str) -> dict:
    try:
        return memory_service.set_memory_item_enabled(memory_id, False)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/items/{memory_id}/enable", response_model=MemoryItem)
def enable_memory_item(memory_id: str) -> dict:
    try:
        return memory_service.set_memory_item_enabled(memory_id, True)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reset")
def reset_memory(request: MemoryResetRequest) -> dict:
    return memory_service.reset_memory(
        scope=request.scope,
        paper_id=request.paper_id,
        memory_type=request.memory_type,
    )


@router.get("/session-memories", response_model=SessionMemoryListResponse)
def list_session_memories() -> dict:
    items = short_term_memory_service.list_session_memory_views()
    return {"items": items, "total": len(items)}


@router.get("/session-memories/{conversation_id}", response_model=SessionMemoryView)
def get_session_memory_view(conversation_id: str) -> dict:
    try:
        return short_term_memory_service.get_session_memory_view(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/session-summaries", response_model=SessionSummaryListResponse)
def list_session_summaries() -> dict:
    items = short_term_memory_service.list_session_summary_views()
    return {"items": items, "total": len(items)}


@router.get("/session-summaries/{conversation_id}", response_model=SessionSummaryView)
def get_session_summary_view(conversation_id: str) -> dict:
    try:
        return short_term_memory_service.get_session_summary_view(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/session-memories/{conversation_id}/clear", response_model=SessionMemoryView)
def clear_session_memory(conversation_id: str) -> dict:
    try:
        short_term_memory_service.clear_short_term_memory(conversation_id)
        return short_term_memory_service.get_session_memory_view(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
