from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaperStructureModel(Base):
    __tablename__ = "paper_structures"

    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class PaperOverviewModel(Base):
    __tablename__ = "paper_overviews"

    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class ReadingMemoryModel(Base):
    __tablename__ = "reading_memories"

    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id"), primary_key=True)
    progress_status: Mapped[str] = mapped_column(String(32), default="new")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    last_read_section: Mapped[str] = mapped_column(String(255), default="Introduction")
    stuck_points: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_questions: Mapped[list[str]] = mapped_column(JSON, default=list)


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[str] = mapped_column(String(64))


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("chat_sessions.session_id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content_md: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String(64))
