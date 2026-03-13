from app.db.base import Base
from app.db.session import engine
from app.models.artifacts import ChatMessageModel, ChatSessionModel, PaperOverviewModel, PaperStructureModel, ReadingMemoryModel
from app.models.paper import IngestionJobModel, PaperModel


def create_all_tables() -> None:
    _ = (
        ChatMessageModel,
        ChatSessionModel,
        PaperOverviewModel,
        PaperStructureModel,
        ReadingMemoryModel,
        IngestionJobModel,
        PaperModel,
    )
    Base.metadata.create_all(bind=engine)
