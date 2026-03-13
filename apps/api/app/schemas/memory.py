from pydantic import BaseModel


class MemoryOverviewResponse(BaseModel):
    read_papers: int
    weak_concepts: list[str]
    preferred_explanation_style: str
    active_topics: list[str]
    recent_stuck_points: list[dict]


class ReadingMemoryResponse(BaseModel):
    paper_id: str
    progress_status: str
    progress_percent: int
    last_read_section: str
    stuck_points: list[str]
    key_questions: list[str]
