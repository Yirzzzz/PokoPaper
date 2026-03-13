from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.db.session import get_session
from app.models.artifacts import (
    ChatMessageModel,
    ChatSessionModel,
    PaperOverviewModel,
    PaperStructureModel,
    ReadingMemoryModel,
)
from app.models.paper import IngestionJobModel, PaperModel


class PostgresStoreRepository:
    def save_file(self, paper_id: str, filename: str, content: bytes) -> str:
        # File storage remains on local disk even when metadata is in PostgreSQL.
        from app.repositories.local_store import LocalStoreRepository

        return LocalStoreRepository().save_file(paper_id=paper_id, filename=filename, content=content)

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

    def create_chat_session(self, session_data: dict[str, Any]) -> dict[str, Any]:
        with get_session() as session:
            session.add(ChatSessionModel(**session_data))
            session.commit()
            return deepcopy(session_data)

    def create_chat_message(self, message: dict[str, Any]) -> dict[str, Any]:
        with get_session() as session:
            payload = {"citations": [], **message}
            session.add(ChatMessageModel(**payload))
            session.commit()
            return deepcopy(payload)

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        with get_session() as session:
            messages = session.scalars(
                select(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
            ).all()
            return [
                {
                    "message_id": item.message_id,
                    "session_id": item.session_id,
                    "role": item.role,
                    "content_md": item.content_md,
                    "citations": deepcopy(item.citations),
                    "created_at": item.created_at,
                }
                for item in messages
            ]

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
