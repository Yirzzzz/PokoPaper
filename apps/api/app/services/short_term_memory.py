from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.repositories.factory import get_repository

INSTANT_MEMORY_QA_WINDOW = 5
INSTANT_MEMORY_MESSAGE_WINDOW = INSTANT_MEMORY_QA_WINDOW * 2


class ShortTermMemoryService:
    def __init__(self) -> None:
        self.repo = get_repository()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _looks_like_low_signal(question: str) -> bool:
        normalized = question.strip().lower()
        return normalized in {"", "你好", "谢谢", "继续", "好的", "嗯", "ok", "okay"} or len(normalized) <= 2

    @staticmethod
    def _session_scope(conversation_id: str) -> str:
        return f"session:{conversation_id}"

    def get_short_term_memory(self, conversation_id: str) -> dict[str, Any]:
        if not hasattr(self.repo, "get_scoped_memory"):
            return {
                "scope_type": "session",
                "scope_id": conversation_id,
                "recent_questions": [],
                "recent_turn_summaries": [],
                "rolling_summary": "",
                "updated_at": "",
            }
        stored = self.repo.get_scoped_memory(self._session_scope(conversation_id)) or {}
        return {
            "scope_type": "session",
            "scope_id": conversation_id,
            "recent_questions": stored.get("recent_questions", []),
            "recent_turn_summaries": stored.get("recent_turn_summaries", []),
            "rolling_summary": stored.get("rolling_summary", ""),
            "updated_at": stored.get("updated_at", ""),
        }

    def get_recent_messages(self, conversation_id: str, limit: int = INSTANT_MEMORY_MESSAGE_WINDOW) -> list[dict[str, Any]]:
        if not hasattr(self.repo, "list_chat_messages"):
            return []
        messages = self.repo.list_chat_messages(conversation_id)
        if limit <= 0:
            return messages
        return messages[-limit:]

    def build_context(self, conversation_id: str, current_question: str | None = None) -> dict[str, Any]:
        memory = self.get_short_term_memory(conversation_id)
        recent_messages = self.get_recent_messages(conversation_id, limit=INSTANT_MEMORY_MESSAGE_WINDOW)
        normalized_current = (current_question or "").strip()

        user_messages = [item for item in recent_messages if item.get("role") == "user"]
        prior_user_messages = user_messages
        if normalized_current and user_messages and (user_messages[-1].get("content_md") or "").strip() == normalized_current:
            prior_user_messages = user_messages[:-1]

        last_user_question = prior_user_messages[-1].get("content_md") if prior_user_messages else None
        last_assistant_message = next(
            (item.get("content_md") for item in reversed(recent_messages) if item.get("role") == "assistant"),
            None,
        )
        return {
            "conversation_id": conversation_id,
            "recent_messages": [
                {
                    "message_id": item.get("message_id", ""),
                    "role": item.get("role"),
                    "content_md": item.get("content_md", ""),
                    "created_at": item.get("created_at", ""),
                }
                for item in recent_messages[-INSTANT_MEMORY_MESSAGE_WINDOW:]
            ],
            "recent_questions": memory.get("recent_questions", [])[-INSTANT_MEMORY_QA_WINDOW:],
            "rolling_summary": memory.get("rolling_summary", ""),
            "updated_at": memory.get("updated_at", ""),
            "last_user_question": last_user_question or (memory.get("recent_questions") or [None])[-1],
            "last_assistant_message": last_assistant_message,
            "has_history": bool(recent_messages or memory.get("recent_questions") or memory.get("rolling_summary")),
        }

    def update_short_term_memory(
        self,
        conversation_id: str,
        question: str,
        answer: str,
    ) -> dict[str, Any]:
        memory = self.get_short_term_memory(conversation_id)
        if self._looks_like_low_signal(question):
            updated = {
                **memory,
                "updated_at": self._now(),
            }
        else:
            recent_questions = [*memory.get("recent_questions", []), question][-INSTANT_MEMORY_QA_WINDOW:]
            prior_turn_summaries = memory.get("recent_turn_summaries", [])
            answer_preview = " ".join(answer.split())[:180]
            turn_summary = f"Q: {question} | A: {answer_preview}"
            recent_turn_summaries = [*prior_turn_summaries, turn_summary][-INSTANT_MEMORY_QA_WINDOW:]
            rolling_summary = "\n".join(recent_turn_summaries)
            updated = {
                **memory,
                "recent_questions": recent_questions,
                "recent_turn_summaries": recent_turn_summaries,
                "rolling_summary": rolling_summary[-1200:],
                "updated_at": self._now(),
            }
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self._session_scope(conversation_id), updated)
        return updated

    def clear_short_term_memory(self, conversation_id: str) -> dict[str, Any]:
        cleared = {
            "scope_type": "session",
            "scope_id": conversation_id,
            "recent_questions": [],
            "recent_turn_summaries": [],
            "rolling_summary": "",
            "updated_at": self._now(),
        }
        if hasattr(self.repo, "delete_chat_messages"):
            self.repo.delete_chat_messages(conversation_id)
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self._session_scope(conversation_id), cleared)
        return cleared

    def list_session_memory_views(self) -> list[dict[str, Any]]:
        sessions = self.repo.list_chat_sessions() if hasattr(self.repo, "list_chat_sessions") else []
        papers = self.repo.list_papers() if hasattr(self.repo, "list_papers") else []
        paper_map = {paper["id"]: paper for paper in papers}
        return [self._build_session_memory_view(session, paper_map) for session in sessions]

    def get_session_memory_view(self, conversation_id: str) -> dict[str, Any]:
        session = self.repo.get_chat_session(conversation_id) if hasattr(self.repo, "get_chat_session") else None
        if session is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        papers = self.repo.list_papers() if hasattr(self.repo, "list_papers") else []
        paper_map = {paper["id"]: paper for paper in papers}
        return self._build_session_memory_view(session, paper_map)

    def _build_session_memory_view(
        self,
        session: dict[str, Any],
        paper_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        conversation_id = session["session_id"]
        context = self.build_context(conversation_id)
        paper_id = session.get("paper_id")
        paper_title = paper_map.get(paper_id or "", {}).get("title") if paper_id else None
        recent_messages = context.get("recent_messages", [])
        recent_questions = context.get("recent_questions", [])
        rolling_summary = context.get("rolling_summary", "")
        is_empty = not recent_messages and not recent_questions and not rolling_summary
        return {
            "conversation_id": conversation_id,
            "conversation_type": session.get("conversation_type", ""),
            "title": session.get("title") or "Untitled Conversation",
            "paper_id": paper_id,
            "paper_title": paper_title,
            "created_at": session.get("created_at") or "",
            "updated_at": context.get("updated_at") or session.get("updated_at") or session.get("created_at") or "",
            "is_empty": is_empty,
            "recent_questions": recent_questions,
            "rolling_summary": rolling_summary,
            "recent_messages": recent_messages,
            "recent_messages_count": len(recent_messages),
        }
