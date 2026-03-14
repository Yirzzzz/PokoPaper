from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from app.repositories.factory import get_repository
from app.services.llm.service import LLMService
from app.schemas.memory import SessionSummaryRecord

INSTANT_MEMORY_QA_WINDOW = 5
RECENT_MESSAGE_WINDOW = 8
SUMMARY_TRIGGER_THRESHOLD = 4


class ShortTermMemoryService:
    def __init__(self) -> None:
        self.repo = get_repository()
        self.llm_service = LLMService()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _looks_like_low_signal(text: str) -> bool:
        normalized = text.strip().lower()
        return normalized in {"", "你好", "谢谢", "继续", "好的", "嗯", "ok", "okay", "展开一点"} or len(normalized) <= 2

    @staticmethod
    def _session_scope(conversation_id: str) -> str:
        return f"session:{conversation_id}"

    @staticmethod
    def _default_session_summary() -> dict[str, Any]:
        return SessionSummaryRecord().model_dump()

    def get_short_term_memory(self, conversation_id: str) -> dict[str, Any]:
        if not hasattr(self.repo, "get_scoped_memory"):
            return {
                "scope_type": "session",
                "scope_id": conversation_id,
                "recent_questions": [],
                "recent_turn_summaries": [],
                "rolling_summary": "",
                "pending_messages": [],
                "session_summary": self._default_session_summary(),
                "updated_at": "",
            }
        stored = self.repo.get_scoped_memory(self._session_scope(conversation_id)) or {}
        return {
            "scope_type": "session",
            "scope_id": conversation_id,
            "recent_questions": stored.get("recent_questions", []),
            "recent_turn_summaries": stored.get("recent_turn_summaries", []),
            "rolling_summary": stored.get("rolling_summary", ""),
            "pending_messages": stored.get("pending_messages", []),
            "session_summary": {
                **self._default_session_summary(),
                **(stored.get("session_summary") or {}),
            },
            "updated_at": stored.get("updated_at", ""),
        }

    def get_recent_messages(self, conversation_id: str, limit: int = RECENT_MESSAGE_WINDOW) -> list[dict[str, Any]]:
        if not hasattr(self.repo, "list_chat_messages"):
            return []
        messages = self.repo.list_chat_messages(conversation_id)
        if limit <= 0:
            return messages
        return messages[-limit:]

    def build_context(self, conversation_id: str, current_question: str | None = None) -> dict[str, Any]:
        memory = self.get_short_term_memory(conversation_id)
        recent_messages = self.get_recent_messages(conversation_id, limit=RECENT_MESSAGE_WINDOW)
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
        session_summary = memory.get("session_summary") or self._default_session_summary()
        return {
            "conversation_id": conversation_id,
            "recent_messages": [
                {
                    "message_id": item.get("message_id", ""),
                    "role": item.get("role"),
                    "content_md": item.get("content_md", ""),
                    "created_at": item.get("created_at", ""),
                }
                for item in recent_messages[-RECENT_MESSAGE_WINDOW:]
            ],
            "recent_questions": memory.get("recent_questions", [])[-INSTANT_MEMORY_QA_WINDOW:],
            "session_summary": session_summary,
            "rolling_summary": session_summary.get("summary_text", ""),
            "updated_at": memory.get("updated_at", ""),
            "last_user_question": last_user_question or (memory.get("recent_questions") or [None])[-1],
            "last_assistant_message": last_assistant_message,
            "has_history": bool(
                recent_messages
                or memory.get("recent_questions")
                or session_summary.get("summary_text")
                or session_summary.get("key_points")
            ),
        }

    def update_short_term_memory(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        selected_model: str | None = None,
    ) -> dict[str, Any]:
        memory = self.get_short_term_memory(conversation_id)
        recent_questions = memory.get("recent_questions", [])
        recent_turn_summaries = memory.get("recent_turn_summaries", [])
        if not self._looks_like_low_signal(question):
            recent_questions = [*recent_questions, question][-INSTANT_MEMORY_QA_WINDOW:]
            answer_preview = " ".join(answer.split())[:180]
            recent_turn_summaries = [*recent_turn_summaries, f"Q: {question} | A: {answer_preview}"][-INSTANT_MEMORY_QA_WINDOW:]

        all_messages = self._messages_for_memory_update(conversation_id, question, answer)
        expired_messages = all_messages[:-RECENT_MESSAGE_WINDOW] if len(all_messages) > RECENT_MESSAGE_WINDOW else []
        pending_messages = memory.get("pending_messages", [])
        new_expired_messages = self._collect_new_expired_messages(
            expired_messages=expired_messages,
            covered_message_until=(memory.get("session_summary") or {}).get("covered_message_until", ""),
            pending_messages=pending_messages,
        )
        pending_messages = [*pending_messages, *new_expired_messages]
        session_summary = memory.get("session_summary") or self._default_session_summary()
        if len(pending_messages) >= SUMMARY_TRIGGER_THRESHOLD:
            session_summary = self._update_session_summary(
                existing_summary=session_summary,
                new_messages=pending_messages,
                selected_model=selected_model,
            )
            pending_messages = []

        updated = {
            **memory,
            "recent_questions": recent_questions,
            "recent_turn_summaries": recent_turn_summaries,
            "rolling_summary": session_summary.get("summary_text", ""),
            "pending_messages": pending_messages,
            "session_summary": session_summary,
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
            "pending_messages": [],
            "session_summary": self._default_session_summary(),
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

    def list_session_summary_views(self) -> list[dict[str, Any]]:
        sessions = self.repo.list_chat_sessions() if hasattr(self.repo, "list_chat_sessions") else []
        papers = self.repo.list_papers() if hasattr(self.repo, "list_papers") else []
        paper_map = {paper["id"]: paper for paper in papers}
        return [self._build_session_summary_view(session, paper_map) for session in sessions]

    def get_session_summary_view(self, conversation_id: str) -> dict[str, Any]:
        session = self.repo.get_chat_session(conversation_id) if hasattr(self.repo, "get_chat_session") else None
        if session is None:
            raise KeyError(f"conversation not found: {conversation_id}")
        papers = self.repo.list_papers() if hasattr(self.repo, "list_papers") else []
        paper_map = {paper["id"]: paper for paper in papers}
        return self._build_session_summary_view(session, paper_map)

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

    def _build_session_summary_view(
        self,
        session: dict[str, Any],
        paper_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        conversation_id = session["session_id"]
        memory = self.get_short_term_memory(conversation_id)
        summary = memory.get("session_summary") or self._default_session_summary()
        paper_id = session.get("paper_id")
        paper_title = paper_map.get(paper_id or "", {}).get("title") if paper_id else None
        is_empty = not summary.get("summary_text") and not summary.get("discussion_topics") and not summary.get("key_points")
        return {
            "conversation_id": conversation_id,
            "conversation_type": session.get("conversation_type", ""),
            "title": session.get("title") or "Untitled Conversation",
            "paper_id": paper_id,
            "paper_title": paper_title,
            "created_at": session.get("created_at") or "",
            "updated_at": memory.get("updated_at") or session.get("updated_at") or session.get("created_at") or "",
            "is_empty": is_empty,
            "summary_text": summary.get("summary_text", ""),
            "discussion_topics": summary.get("discussion_topics", []),
            "key_points": summary.get("key_points", []),
            "open_questions": summary.get("open_questions", []),
            "last_updated_at": summary.get("last_updated_at", ""),
            "covered_message_until": summary.get("covered_message_until", ""),
            "pending_messages_count": len(memory.get("pending_messages", [])),
        }

    def _messages_for_memory_update(self, conversation_id: str, question: str, answer: str) -> list[dict[str, Any]]:
        messages = self.repo.list_chat_messages(conversation_id) if hasattr(self.repo, "list_chat_messages") else []
        normalized_question = question.strip()
        if not messages or messages[-1].get("role") != "user" or (messages[-1].get("content_md") or "").strip() != normalized_question:
            messages = [
                *messages,
                {
                    "message_id": f"synthetic-user-{conversation_id}",
                    "role": "user",
                    "content_md": question,
                    "created_at": self._now(),
                },
            ]
        messages = [
            *messages,
            {
                "message_id": f"synthetic-assistant-{conversation_id}",
                "role": "assistant",
                "content_md": answer,
                "created_at": self._now(),
            },
        ]
        return messages

    def _collect_new_expired_messages(
        self,
        expired_messages: list[dict[str, Any]],
        covered_message_until: str,
        pending_messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        pending_ids = {item.get("message_id") for item in pending_messages}
        start_index = 0
        if covered_message_until:
            for index, message in enumerate(expired_messages):
                if message.get("message_id") == covered_message_until:
                    start_index = index + 1
                    break
        new_messages = expired_messages[start_index:]
        return self._filter_summary_messages(
            [
                {
                    "message_id": item.get("message_id", ""),
                    "role": item.get("role"),
                    "content_md": item.get("content_md", ""),
                    "created_at": item.get("created_at", ""),
                }
                for item in new_messages
                if item.get("message_id") not in pending_ids
            ]
        )

    def _filter_summary_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        skip_next_assistant = False
        for message in messages:
            content = (message.get("content_md") or "").strip()
            if message.get("role") == "user" and self._looks_like_low_signal(content):
                skip_next_assistant = True
                continue
            if message.get("role") == "assistant" and skip_next_assistant:
                skip_next_assistant = False
                continue
            skip_next_assistant = False
            if not content:
                continue
            filtered.append(message)
        return filtered

    def _update_session_summary(
        self,
        existing_summary: dict[str, Any],
        new_messages: list[dict[str, Any]],
        selected_model: str | None = None,
    ) -> dict[str, Any]:
        llm_summary = self.llm_service.generate_incremental_session_summary(
            selected_model=selected_model,
            existing_summary=existing_summary,
            new_messages=new_messages,
        )
        if llm_summary:
            return {
                **self._default_session_summary(),
                **llm_summary,
                "last_updated_at": self._now(),
                "covered_message_until": new_messages[-1].get("message_id", existing_summary.get("covered_message_until", "")),
            }
        return self._heuristic_incremental_summary(existing_summary, new_messages)

    def _heuristic_incremental_summary(
        self,
        existing_summary: dict[str, Any],
        new_messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        discussion_topics = list(existing_summary.get("discussion_topics", []))
        key_points = list(existing_summary.get("key_points", []))
        open_questions = list(existing_summary.get("open_questions", []))

        for message in new_messages:
            content = (message.get("content_md") or "").strip()
            if message.get("role") == "user":
                for topic in self._extract_topics(content):
                    if topic not in discussion_topics:
                        discussion_topics.append(topic)
                if self._looks_like_open_question(content):
                    open_questions = self._append_unique(open_questions, content[:140], 5)
            elif content:
                key_points = self._append_unique(key_points, content[:180], 6)

        discussion_topics = discussion_topics[-6:]
        key_points = key_points[-6:]
        open_questions = open_questions[-5:]
        summary_text = self._compose_summary_text(discussion_topics, key_points, open_questions)
        return {
            "summary_text": summary_text,
            "discussion_topics": discussion_topics,
            "key_points": key_points,
            "open_questions": open_questions,
            "last_updated_at": self._now(),
            "covered_message_until": new_messages[-1].get("message_id", existing_summary.get("covered_message_until", "")),
        }

    @staticmethod
    def _append_unique(items: list[str], value: str, limit: int) -> list[str]:
        normalized = value.strip()
        merged = [item for item in items if item != normalized]
        merged.append(normalized)
        return merged[-limit:]

    @staticmethod
    def _looks_like_open_question(content: str) -> bool:
        lowered = content.lower()
        return "?" in content or "？" in content or any(token in lowered for token in ["没懂", "不理解", "why", "how", "what"])

    @staticmethod
    def _extract_topics(content: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9\-\+]{2,}", content)
        topics: list[str] = []
        for candidate in candidates:
            if candidate.lower() in {"what", "why", "how", "this", "that", "with", "from"}:
                continue
            if candidate not in topics:
                topics.append(candidate)
            if len(topics) == 4:
                break
        return topics

    @staticmethod
    def _compose_summary_text(discussion_topics: list[str], key_points: list[str], open_questions: list[str]) -> str:
        parts: list[str] = []
        if discussion_topics:
            parts.append(f"讨论主题：{'、'.join(discussion_topics[:4])}")
        if key_points:
            parts.append(f"重要结论：{'；'.join(key_points[:3])}")
        if open_questions:
            parts.append(f"未解决问题：{'；'.join(open_questions[:2])}")
        return "\n".join(parts)
