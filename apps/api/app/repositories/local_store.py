from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.schemas.chat import ConversationType


class LocalStoreRepository:
    def __init__(self) -> None:
        self.storage_dir = Path(settings.storage_dir)
        self.db_dir = self.storage_dir / "db"
        self.files_dir = self.storage_dir / "papers"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self.db_path = self.db_dir / "store.json"
        if not self.db_path.exists():
            self._write(
                {
                    "papers": [],
                    "jobs": [],
                    "structures": {},
                    "overviews": {},
                    "paper_entity_cards": {},
                    "memories": {},
                    "memory_item_states": {},
                    "memory_item_meta": {},
                    "chat_sessions": [],
                    "chat_messages": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        with self._lock:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        normalized = self._normalize_chat_messages(data)
        normalized = self._normalize_chat_sessions(normalized)
        normalized = self._normalize_scoped_memories(normalized)
        normalized.setdefault("memory_item_states", {})
        normalized.setdefault("memory_item_meta", {})
        if normalized != data:
            self._write(normalized)
        return normalized

    def _write(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.db_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    @staticmethod
    def _normalize_chat_messages(data: dict[str, Any]) -> dict[str, Any]:
        messages = data.get("chat_messages", [])
        seen_ids: set[str] = set()
        changed = False
        normalized_messages: list[dict[str, Any]] = []
        for index, message in enumerate(messages):
            normalized = deepcopy(message)
            message_id = normalized.get("message_id") or f"message-{uuid4().hex[:8]}"
            if message_id in seen_ids:
                normalized["message_id"] = f"{message_id}-{index}-{uuid4().hex[:4]}"
                changed = True
            else:
                normalized["message_id"] = message_id
            seen_ids.add(normalized["message_id"])
            normalized_messages.append(normalized)
        if not changed and len(normalized_messages) == len(messages):
            return data
        return {
            **data,
            "chat_messages": normalized_messages,
        }

    @staticmethod
    def _normalize_chat_sessions(data: dict[str, Any]) -> dict[str, Any]:
        sessions = data.get("chat_sessions", [])
        changed = False
        normalized_sessions: list[dict[str, Any]] = []
        for index, session in enumerate(sessions):
            normalized = deepcopy(session)
            session_id = normalized.get("session_id") or normalized.get("conversation_id") or f"session-{uuid4().hex[:8]}"
            if normalized.get("conversation_id") != session_id:
                normalized["conversation_id"] = session_id
                changed = True
            if normalized.get("session_id") != session_id:
                normalized["session_id"] = session_id
                changed = True

            session_key = normalized.get("session_key")
            paper_id = normalized.get("paper_id")
            inferred_type = normalized.get("conversation_type")
            if inferred_type not in {ConversationType.GLOBAL_CHAT, ConversationType.PAPER_CHAT}:
                if isinstance(session_key, str) and session_key.startswith("main-chat:"):
                    inferred_type = ConversationType.GLOBAL_CHAT
                    if paper_id is not None:
                        normalized["paper_id"] = None
                        changed = True
                elif session_key == "global-chat":
                    inferred_type = ConversationType.GLOBAL_CHAT
                    if paper_id is not None:
                        normalized["paper_id"] = None
                        changed = True
                elif paper_id:
                    inferred_type = ConversationType.PAPER_CHAT
                else:
                    inferred_type = ConversationType.GLOBAL_CHAT
                changed = True
            normalized["conversation_type"] = inferred_type

            created_at = normalized.get("created_at") or "1970-01-01T00:00:00+00:00"
            if "updated_at" not in normalized:
                normalized["updated_at"] = created_at
                changed = True
            if "is_deleted" not in normalized:
                normalized["is_deleted"] = False
                changed = True
            if inferred_type == ConversationType.GLOBAL_CHAT and normalized.get("paper_id") is not None:
                normalized["paper_id"] = None
                changed = True
            normalized_sessions.append(normalized)

        if not changed and len(normalized_sessions) == len(sessions):
            return data
        return {
            **data,
            "chat_sessions": normalized_sessions,
        }

    @staticmethod
    def _normalize_scoped_memories(data: dict[str, Any]) -> dict[str, Any]:
        memories = data.get("memories", {})
        if not isinstance(memories, dict):
            return data
        changed = False
        normalized_memories: dict[str, Any] = {}
        for raw_key, raw_value in memories.items():
            key = str(raw_key)
            if key.startswith(("session:", "paper:", "user:")):
                scoped_key = key
            elif key.startswith("chat-session:"):
                scoped_key = f"session:{key.split(':', 1)[1]}"
                changed = True
            elif key == "local-user":
                scoped_key = "user:local-user"
                changed = True
            elif key.startswith("paper-"):
                scoped_key = f"paper:{key}"
                changed = True
            else:
                scoped_key = key
            normalized_memories[scoped_key] = raw_value
        if not changed and normalized_memories == memories:
            return data
        return {
            **data,
            "memories": normalized_memories,
        }

    def save_file(self, paper_id: str, filename: str, content: bytes) -> str:
        safe_name = filename.replace("/", "_")
        path = self.files_dir / f"{paper_id}-{safe_name}"
        path.write_bytes(content)
        return str(path)

    def list_papers(self) -> list[dict[str, Any]]:
        data = self._read()
        papers = deepcopy(data["papers"])
        papers.sort(key=lambda item: item["created_at"], reverse=True)
        return papers

    def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return next((paper for paper in data["papers"] if paper["id"] == paper_id), None)

    def upsert_paper(self, paper: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        papers = [item for item in data["papers"] if item["id"] != paper["id"]]
        papers.append(paper)
        data["papers"] = papers
        self._write(data)
        return paper

    def delete_paper(self, paper_id: str) -> None:
        data = self._read()
        paper = next((item for item in data["papers"] if item["id"] == paper_id), None)
        if paper is None:
            raise KeyError(f"paper not found: {paper_id}")
        deleted_session_ids = {
            item["session_id"]
            for item in data["chat_sessions"]
            if item["paper_id"] == paper_id and item.get("conversation_type") == ConversationType.PAPER_CHAT
        }
        data["papers"] = [item for item in data["papers"] if item["id"] != paper_id]
        data["jobs"] = [item for item in data["jobs"] if item["paper_id"] != paper_id]
        data["chat_sessions"] = [item for item in data["chat_sessions"] if item["paper_id"] != paper_id]
        valid_session_ids = {item["session_id"] for item in data["chat_sessions"]}
        data["chat_messages"] = [
            item for item in data["chat_messages"] if item["session_id"] in valid_session_ids
        ]
        data["structures"].pop(paper_id, None)
        data["overviews"].pop(paper_id, None)
        data.get("paper_entity_cards", {}).pop(paper_id, None)
        data["memories"].pop(paper_id, None)
        data["memories"].pop(f"paper:{paper_id}", None)
        for session_id in deleted_session_ids:
            data["memories"].pop(f"session:{session_id}", None)
        memory_item_ids_to_remove = [
            memory_id
            for memory_id, meta in data.get("memory_item_meta", {}).items()
            if meta.get("paper_id") == paper_id
        ]
        for memory_id in memory_item_ids_to_remove:
            data.get("memory_item_meta", {}).pop(memory_id, None)
            data.get("memory_item_states", {}).pop(memory_id, None)
        file_path = paper.get("file_path")
        if file_path:
            path = Path(file_path)
            if path.exists():
                path.unlink()
        self._write(data)

    def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        data["jobs"].append(job)
        self._write(data)
        return job

    def update_job(self, job_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        updated = None
        for job in data["jobs"]:
            if job["job_id"] == job_id:
                job.update(patch)
                updated = deepcopy(job)
                break
        self._write(data)
        if updated is None:
            raise KeyError(f"job not found: {job_id}")
        return updated

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        data = self._read()
        return next((job for job in data["jobs"] if job["job_id"] == job_id), None)

    def save_structure(self, paper_id: str, structure: dict[str, Any]) -> None:
        data = self._read()
        data["structures"][paper_id] = structure
        self._write(data)

    def get_structure(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return deepcopy(data["structures"].get(paper_id))

    def save_overview(self, paper_id: str, overview: dict[str, Any]) -> None:
        data = self._read()
        data["overviews"][paper_id] = overview
        self._write(data)

    def get_overview(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return deepcopy(data["overviews"].get(paper_id))

    def save_paper_entity_card(self, paper_id: str, card: dict[str, Any]) -> None:
        data = self._read()
        data.setdefault("paper_entity_cards", {})[paper_id] = card
        self._write(data)

    def get_paper_entity_card(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return deepcopy(data.get("paper_entity_cards", {}).get(paper_id))

    def list_paper_entity_cards(self) -> list[dict[str, Any]]:
        data = self._read()
        items = list(deepcopy(data.get("paper_entity_cards", {})).values())
        items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return items

    def save_memory(self, paper_id: str, memory: dict[str, Any]) -> None:
        data = self._read()
        data["memories"][paper_id] = memory
        self._write(data)

    def get_memory(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return deepcopy(data["memories"].get(paper_id))

    def save_scoped_memory(self, scope_key: str, memory: dict[str, Any]) -> None:
        data = self._read()
        data["memories"][scope_key] = memory
        self._write(data)

    def get_scoped_memory(self, scope_key: str) -> dict[str, Any] | None:
        data = self._read()
        memory = data["memories"].get(scope_key)
        if memory is not None:
            return deepcopy(memory)
        if scope_key.startswith("paper:"):
            legacy_key = scope_key.split(":", 1)[1]
            legacy_memory = data["memories"].get(legacy_key)
            if legacy_memory is not None:
                data["memories"][scope_key] = legacy_memory
                self._write(data)
                return deepcopy(legacy_memory)
        return None

    def list_scoped_memories(self) -> dict[str, Any]:
        data = self._read()
        return deepcopy(data.get("memories", {}))

    def save_memory_item_state(self, memory_id: str, state: dict[str, Any]) -> None:
        data = self._read()
        data.setdefault("memory_item_states", {})[memory_id] = state
        self._write(data)

    def get_memory_item_state(self, memory_id: str) -> dict[str, Any] | None:
        data = self._read()
        state = data.get("memory_item_states", {}).get(memory_id)
        return deepcopy(state) if state else None

    def list_memory_item_states(self) -> dict[str, Any]:
        data = self._read()
        return deepcopy(data.get("memory_item_states", {}))

    def save_memory_item_meta(self, memory_id: str, meta: dict[str, Any]) -> None:
        data = self._read()
        data.setdefault("memory_item_meta", {})[memory_id] = meta
        self._write(data)

    def get_memory_item_meta(self, memory_id: str) -> dict[str, Any] | None:
        data = self._read()
        meta = data.get("memory_item_meta", {}).get(memory_id)
        return deepcopy(meta) if meta else None

    def list_memory_item_meta(self) -> dict[str, Any]:
        data = self._read()
        return deepcopy(data.get("memory_item_meta", {}))

    def delete_memory_item_aux(self, memory_id: str) -> None:
        data = self._read()
        data.get("memory_item_states", {}).pop(memory_id, None)
        data.get("memory_item_meta", {}).pop(memory_id, None)
        self._write(data)

    def create_chat_session(self, session: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        normalized = deepcopy(session)
        session_id = normalized.get("conversation_id") or normalized.get("session_id") or f"session-{uuid4().hex[:8]}"
        created_at = normalized.get("created_at") or "1970-01-01T00:00:00+00:00"
        normalized["conversation_id"] = session_id
        normalized["session_id"] = session_id
        normalized["updated_at"] = normalized.get("updated_at") or created_at
        normalized["is_deleted"] = bool(normalized.get("is_deleted", False))
        normalized["conversation_type"] = normalized.get("conversation_type") or (
            ConversationType.PAPER_CHAT if normalized.get("paper_id") else ConversationType.GLOBAL_CHAT
        )
        if normalized["conversation_type"] == ConversationType.GLOBAL_CHAT:
            normalized["paper_id"] = None
        data["chat_sessions"] = [
            item for item in data["chat_sessions"] if item["session_id"] != normalized["session_id"]
        ]
        data["chat_sessions"].append(normalized)
        self._write(data)
        return deepcopy(normalized)

    def get_chat_session_by_paper(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        sessions = [
            item
            for item in data["chat_sessions"]
            if item["paper_id"] == paper_id
            and item.get("conversation_type") == ConversationType.PAPER_CHAT
            and not item.get("is_deleted", False)
        ]
        if not sessions:
            return None
        sessions.sort(key=lambda item: item["created_at"])
        return deepcopy(sessions[0])

    def get_chat_session_by_key(self, session_key: str) -> dict[str, Any] | None:
        data = self._read()
        sessions = [
            item
            for item in data["chat_sessions"]
            if item.get("session_key") == session_key and not item.get("is_deleted", False)
        ]
        if not sessions:
            return None
        sessions.sort(key=lambda item: item["created_at"])
        return deepcopy(sessions[0])

    def get_chat_session(self, session_id: str) -> dict[str, Any] | None:
        data = self._read()
        session = next(
            (
                item
                for item in data["chat_sessions"]
                if item["session_id"] == session_id and not item.get("is_deleted", False)
            ),
            None,
        )
        return deepcopy(session) if session else None

    def list_global_chat_sessions(self) -> list[dict[str, Any]]:
        data = self._read()
        sessions = [
            item
            for item in data["chat_sessions"]
            if item.get("conversation_type") == ConversationType.GLOBAL_CHAT and not item.get("is_deleted", False)
        ]
        sessions.sort(key=lambda item: item.get("updated_at") or item["created_at"], reverse=True)
        return deepcopy(sessions)

    def list_chat_sessions(self) -> list[dict[str, Any]]:
        data = self._read()
        sessions = [
            item
            for item in data["chat_sessions"]
            if not item.get("is_deleted", False)
        ]
        sessions.sort(key=lambda item: item.get("updated_at") or item["created_at"], reverse=True)
        return deepcopy(sessions)

    def update_chat_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        updated = None
        for item in data["chat_sessions"]:
            if item["session_id"] == session_id:
                item.update(patch)
                updated = deepcopy(item)
                break
        if updated is None:
            raise KeyError(f"chat session not found: {session_id}")
        self._write(data)
        return updated

    def delete_global_chat_session(self, session_id: str) -> None:
        session = self.get_chat_session(session_id)
        if session is None:
            raise KeyError(f"chat session not found: {session_id}")
        if session.get("conversation_type") != ConversationType.GLOBAL_CHAT:
            raise ValueError("only global_chat conversations can be deleted")
        self.update_chat_session(
            session_id,
            {
                "is_deleted": True,
                "updated_at": session.get("updated_at") or session.get("created_at"),
            },
        )

    def create_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        session_id = message["session_id"]
        data["chat_messages"].append(message)
        for item in data["chat_sessions"]:
            if item["session_id"] == session_id:
                item["updated_at"] = message["created_at"]
                break
        self._write(data)
        return message

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        data = self._read()
        messages = [message for message in data["chat_messages"] if message["session_id"] == session_id]
        messages.sort(key=lambda item: item["created_at"])
        return deepcopy(messages)

    def delete_chat_messages(self, session_id: str) -> None:
        data = self._read()
        data["chat_messages"] = [
            message for message in data["chat_messages"] if message["session_id"] != session_id
        ]
        self._write(data)
