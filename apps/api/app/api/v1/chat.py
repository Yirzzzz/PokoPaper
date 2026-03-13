from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter

from app.agents.paper_companion_agent import PaperCompanionAgent
from app.repositories.factory import get_repository
from app.schemas.chat import (
    ChatHistoryMessage,
    ChatMessageRequest,
    ChatMessageResponse,
    CreateChatSessionRequest,
    CreateChatSessionResponse,
)
from app.schemas.models import ChatModelOption
from app.services.llm.service import LLMService

router = APIRouter()
agent = PaperCompanionAgent()
repo = get_repository()
llm_service = LLMService()


@router.post("/sessions", response_model=CreateChatSessionResponse)
def create_chat_session(payload: CreateChatSessionRequest) -> dict:
    existing = repo.get_chat_session_by_paper(payload.paper_id)
    if existing is not None:
        return existing
    session = {
        "session_id": f"session-{uuid4().hex[:8]}",
        "paper_id": payload.paper_id,
        "title": "PokeRAG Reading Session",
        "created_at": datetime.now(UTC).isoformat(),
    }
    repo.create_chat_session(session)
    return session


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def create_chat_message(session_id: str, payload: ChatMessageRequest) -> dict:
    repo.create_chat_message(
        {
            "message_id": f"message-user-{uuid4().hex[:8]}",
            "session_id": session_id,
            "role": "user",
            "content_md": payload.question,
            "citations": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    answer = agent.answer(
        paper_id=payload.paper_id,
        question=payload.question,
        selected_model=payload.selected_model,
        enable_thinking=payload.enable_thinking,
    )
    repo.create_chat_message(
        {
            "message_id": answer["message_id"],
            "session_id": session_id,
            "role": "assistant",
            "content_md": answer["answer_md"],
            "citations": answer["citations"],
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    return answer


@router.get("/sessions/by-paper/{paper_id}", response_model=CreateChatSessionResponse)
def get_or_create_chat_session_for_paper(paper_id: str) -> dict:
    existing = repo.get_chat_session_by_paper(paper_id)
    if existing is not None:
        return existing
    session = {
        "session_id": f"session-{uuid4().hex[:8]}",
        "paper_id": paper_id,
        "title": "PokeRAG Reading Session",
        "created_at": datetime.now(UTC).isoformat(),
    }
    repo.create_chat_session(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatHistoryMessage])
def list_chat_messages(session_id: str) -> list[dict]:
    return repo.list_chat_messages(session_id)


@router.get("/models", response_model=list[ChatModelOption])
def list_chat_models() -> list[dict]:
    return llm_service.list_models()
