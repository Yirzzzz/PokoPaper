from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response, status

from app.agents.paper_companion_agent import PaperCompanionAgent
from app.repositories.factory import get_repository
from app.schemas.chat import (
    ChatHistoryMessage,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationType,
    CreateGlobalConversationRequest,
    CreateChatSessionRequest,
    CreateChatSessionResponse,
    ListConversationsResponse,
)
from app.schemas.models import ChatModelOption
from app.services.llm.service import LLMService

router = APIRouter()
agent = PaperCompanionAgent()
repo = get_repository()
llm_service = LLMService()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _serialize_conversation(session: dict) -> dict:
    conversation_id = session.get("conversation_id") or session["session_id"]
    created_at = session.get("created_at") or _now()
    return {
        "conversation_id": conversation_id,
        "session_id": conversation_id,
        "conversation_type": session.get("conversation_type") or (
            ConversationType.PAPER_CHAT if session.get("paper_id") else ConversationType.GLOBAL_CHAT
        ),
        "paper_id": session.get("paper_id"),
        "title": session.get("title") or "Untitled Conversation",
        "created_at": created_at,
        "updated_at": session.get("updated_at") or created_at,
        "is_deleted": bool(session.get("is_deleted", False)),
    }


@router.post("/sessions", response_model=CreateChatSessionResponse)
def create_chat_session(payload: CreateChatSessionRequest) -> dict:
    return get_or_create_chat_session_for_paper(payload.paper_id)


@router.get("/conversations/global", response_model=ListConversationsResponse)
def list_global_conversations() -> dict:
    conversations = repo.list_global_chat_sessions() if hasattr(repo, "list_global_chat_sessions") else []
    return {"conversations": [_serialize_conversation(item) for item in conversations]}


@router.post("/conversations/global", response_model=CreateChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_global_conversation(payload: CreateGlobalConversationRequest) -> dict:
    now = _now()
    conversation_id = f"session-{uuid4().hex[:8]}"
    conversation = repo.create_chat_session(
        {
            "conversation_id": conversation_id,
            "session_id": conversation_id,
            "conversation_type": ConversationType.GLOBAL_CHAT,
            "paper_id": None,
            "session_key": None,
            "title": payload.title or "New Global Conversation",
            "created_at": now,
            "updated_at": now,
            "is_deleted": False,
        }
    )
    return _serialize_conversation(conversation)


@router.delete("/conversations/global/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_global_conversation(conversation_id: str) -> Response:
    try:
        repo.delete_global_chat_session(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def create_chat_message(session_id: str, payload: ChatMessageRequest) -> dict:
    session = repo.get_chat_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found")
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
        session_id=session_id,
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
        return _serialize_conversation(existing)
    now = _now()
    conversation_id = f"session-{uuid4().hex[:8]}"
    session = {
        "session_id": conversation_id,
        "conversation_id": conversation_id,
        "conversation_type": ConversationType.PAPER_CHAT,
        "paper_id": paper_id,
        "title": "PokeRAG Reading Session",
        "created_at": now,
        "updated_at": now,
        "is_deleted": False,
    }
    created = repo.create_chat_session(session)
    return _serialize_conversation(created)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatHistoryMessage])
def list_chat_messages(session_id: str) -> list[dict]:
    return repo.list_chat_messages(session_id)


@router.get("/models", response_model=list[ChatModelOption])
def list_chat_models() -> list[dict]:
    return llm_service.list_models()
