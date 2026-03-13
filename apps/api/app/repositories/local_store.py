from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.config import settings


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
                    "memories": {},
                    "chat_sessions": [],
                    "chat_messages": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        with self._lock:
            data = json.loads(self.db_path.read_text(encoding="utf-8"))
        normalized = self._normalize_chat_messages(data)
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
        data["papers"] = [item for item in data["papers"] if item["id"] != paper_id]
        data["jobs"] = [item for item in data["jobs"] if item["paper_id"] != paper_id]
        data["chat_sessions"] = [item for item in data["chat_sessions"] if item["paper_id"] != paper_id]
        valid_session_ids = {item["session_id"] for item in data["chat_sessions"]}
        data["chat_messages"] = [
            item for item in data["chat_messages"] if item["session_id"] in valid_session_ids
        ]
        data["structures"].pop(paper_id, None)
        data["overviews"].pop(paper_id, None)
        data["memories"].pop(paper_id, None)
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

    def save_memory(self, paper_id: str, memory: dict[str, Any]) -> None:
        data = self._read()
        data["memories"][paper_id] = memory
        self._write(data)

    def get_memory(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        return deepcopy(data["memories"].get(paper_id))

    def create_chat_session(self, session: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        data["chat_sessions"].append(session)
        self._write(data)
        return session

    def get_chat_session_by_paper(self, paper_id: str) -> dict[str, Any] | None:
        data = self._read()
        sessions = [item for item in data["chat_sessions"] if item["paper_id"] == paper_id]
        if not sessions:
            return None
        sessions.sort(key=lambda item: item["created_at"])
        return deepcopy(sessions[0])

    def create_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        data["chat_messages"].append(message)
        self._write(data)
        return message

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        data = self._read()
        messages = [message for message in data["chat_messages"] if message["session_id"] == session_id]
        messages.sort(key=lambda item: item["created_at"])
        return deepcopy(messages)
