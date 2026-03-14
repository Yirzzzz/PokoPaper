from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.db.session import get_session
from app.models.artifacts import (
    PaperOverviewModel,
    PaperStructureModel,
    ReadingMemoryModel,
)
from app.models.paper import IngestionJobModel, PaperModel


class PostgresStoreRepository:
    @staticmethod
    def _local_store():
        from app.repositories.local_store import LocalStoreRepository

        return LocalStoreRepository()

    def save_file(self, paper_id: str, filename: str, content: bytes) -> str:
        # File storage remains on local disk even when metadata is in PostgreSQL.
        return self._local_store().save_file(paper_id=paper_id, filename=filename, content=content)

    def list_papers(self) -> list[dict[str, Any]]:
        with get_session() as session:
            papers = session.scalars(select(PaperModel).order_by(PaperModel.created_at.desc())).all()
            return [self._paper_to_dict(item) for item in papers]

    def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        with get_session() as session:
            paper = session.get(PaperModel, paper_id)
            return self._paper_to_dict(paper) if paper else None

    def upsert_paper(self, paper: dict[str, Any]) -> dict[str, Any]:
        payload = {
            **paper,
            "created_at": self._coerce_datetime(paper["created_at"]),
            "updated_at": self._coerce_datetime(paper["updated_at"]),
        }
        with get_session() as session:
            model = session.get(PaperModel, paper["id"])
            if model is None:
                model = PaperModel(**payload)
                session.add(model)
            else:
                for key, value in payload.items():
                    setattr(model, key, value)
            session.commit()
            return deepcopy(paper)

    def create_job(self, job: dict[str, Any]) -> dict[str, Any]:
        payload = {
            **job,
            "created_at": self._coerce_datetime(job["created_at"]),
            "updated_at": self._coerce_datetime(job["updated_at"]),
        }
        with get_session() as session:
            session.add(IngestionJobModel(**payload))
            session.commit()
            return deepcopy(job)

    def update_job(self, job_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(patch)
        if "created_at" in payload:
            payload["created_at"] = self._coerce_datetime(payload["created_at"])
        if "updated_at" in payload:
            payload["updated_at"] = self._coerce_datetime(payload["updated_at"])
        with get_session() as session:
            job = session.get(IngestionJobModel, job_id)
            if job is None:
                raise KeyError(f"job not found: {job_id}")
            for key, value in payload.items():
                setattr(job, key, value)
            session.commit()
            return self._job_to_dict(job)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with get_session() as session:
            job = session.get(IngestionJobModel, job_id)
            return self._job_to_dict(job) if job else None

    def save_structure(self, paper_id: str, structure: dict[str, Any]) -> None:
        with get_session() as session:
            model = session.get(PaperStructureModel, paper_id)
            if model is None:
                model = PaperStructureModel(paper_id=paper_id, payload=structure)
                session.add(model)
            else:
                model.payload = structure
            session.commit()

    def get_structure(self, paper_id: str) -> dict[str, Any] | None:
        with get_session() as session:
            model = session.get(PaperStructureModel, paper_id)
            return deepcopy(model.payload) if model else None

    def save_overview(self, paper_id: str, overview: dict[str, Any]) -> None:
        with get_session() as session:
            model = session.get(PaperOverviewModel, paper_id)
            if model is None:
                model = PaperOverviewModel(paper_id=paper_id, payload=overview)
                session.add(model)
            else:
                model.payload = overview
            session.commit()

    def get_overview(self, paper_id: str) -> dict[str, Any] | None:
        with get_session() as session:
            model = session.get(PaperOverviewModel, paper_id)
            return deepcopy(model.payload) if model else None

    def save_paper_entity_card(self, paper_id: str, card: dict[str, Any]) -> None:
        self._local_store().save_paper_entity_card(paper_id, card)

    def get_paper_entity_card(self, paper_id: str) -> dict[str, Any] | None:
        return self._local_store().get_paper_entity_card(paper_id)

    def list_paper_entity_cards(self) -> list[dict[str, Any]]:
        return self._local_store().list_paper_entity_cards()

    def save_memory(self, paper_id: str, memory: dict[str, Any]) -> None:
        with get_session() as session:
            model = session.get(ReadingMemoryModel, paper_id)
            if model is None:
                model = ReadingMemoryModel(**memory)
                session.add(model)
            else:
                for key, value in memory.items():
                    setattr(model, key, value)
            session.commit()

    def get_memory(self, paper_id: str) -> dict[str, Any] | None:
        with get_session() as session:
            model = session.get(ReadingMemoryModel, paper_id)
            if model is None:
                return None
            return {
                "paper_id": model.paper_id,
                "progress_status": model.progress_status,
                "progress_percent": model.progress_percent,
                "last_read_section": model.last_read_section,
                "stuck_points": deepcopy(model.stuck_points),
                "key_questions": deepcopy(model.key_questions),
            }

    def save_scoped_memory(self, scope_key: str, memory: dict[str, Any]) -> None:
        self._local_store().save_scoped_memory(scope_key, memory)

    def get_scoped_memory(self, scope_key: str) -> dict[str, Any] | None:
        return self._local_store().get_scoped_memory(scope_key)

    def list_scoped_memories(self) -> dict[str, Any]:
        return self._local_store().list_scoped_memories()

    def save_memory_item_state(self, memory_id: str, state: dict[str, Any]) -> None:
        self._local_store().save_memory_item_state(memory_id, state)

    def get_memory_item_state(self, memory_id: str) -> dict[str, Any] | None:
        return self._local_store().get_memory_item_state(memory_id)

    def list_memory_item_states(self) -> dict[str, Any]:
        return self._local_store().list_memory_item_states()

    def save_memory_item_meta(self, memory_id: str, meta: dict[str, Any]) -> None:
        self._local_store().save_memory_item_meta(memory_id, meta)

    def get_memory_item_meta(self, memory_id: str) -> dict[str, Any] | None:
        return self._local_store().get_memory_item_meta(memory_id)

    def list_memory_item_meta(self) -> dict[str, Any]:
        return self._local_store().list_memory_item_meta()

    def delete_memory_item_aux(self, memory_id: str) -> None:
        self._local_store().delete_memory_item_aux(memory_id)

    def create_chat_session(self, session_data: dict[str, Any]) -> dict[str, Any]:
        return self._local_store().create_chat_session(session_data)

    def get_chat_session_by_paper(self, paper_id: str) -> dict[str, Any] | None:
        return self._local_store().get_chat_session_by_paper(paper_id)

    def get_chat_session_by_key(self, session_key: str) -> dict[str, Any] | None:
        return self._local_store().get_chat_session_by_key(session_key)

    def get_chat_session(self, session_id: str) -> dict[str, Any] | None:
        return self._local_store().get_chat_session(session_id)

    def list_global_chat_sessions(self) -> list[dict[str, Any]]:
        return self._local_store().list_global_chat_sessions()

    def list_chat_sessions(self) -> list[dict[str, Any]]:
        return self._local_store().list_chat_sessions()

    def update_chat_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return self._local_store().update_chat_session(session_id, patch)

    def delete_global_chat_session(self, session_id: str) -> None:
        self._local_store().delete_global_chat_session(session_id)

    def create_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        return self._local_store().create_chat_message(message)

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        return self._local_store().list_chat_messages(session_id)

    def delete_chat_messages(self, session_id: str) -> None:
        self._local_store().delete_chat_messages(session_id)

    @staticmethod
    def _paper_to_dict(model: PaperModel) -> dict[str, Any]:
        return {
            "id": model.id,
            "title": model.title,
            "authors": deepcopy(model.authors),
            "abstract": model.abstract,
            "status": model.status,
            "progress_percent": model.progress_percent,
            "file_path": model.file_path,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
        }

    @staticmethod
    def _job_to_dict(model: IngestionJobModel) -> dict[str, Any]:
        return {
            "job_id": model.job_id,
            "paper_id": model.paper_id,
            "status": model.status,
            "stage": model.stage,
            "progress": model.progress,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
        }

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise TypeError(f"Unsupported datetime value: {value!r}")
