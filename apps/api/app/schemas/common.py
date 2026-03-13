from pydantic import BaseModel


class Citation(BaseModel):
    chunk_id: str
    section_title: str
    page_num: int
    support_level: str = "explicit"


class RecommendationItem(BaseModel):
    type: str
    title: str
    reason: str
    relation_to_current_paper: str
    suggested_section: str
    difficulty_level: str
