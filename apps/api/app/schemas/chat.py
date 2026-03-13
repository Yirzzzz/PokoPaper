from pydantic import BaseModel

from app.schemas.common import Citation, RecommendationItem


class CreateChatSessionRequest(BaseModel):
    paper_id: str


class CreateChatSessionResponse(BaseModel):
    session_id: str
    paper_id: str
    title: str


class ChatMessageRequest(BaseModel):
    paper_id: str
    question: str
    selected_model: str | None = None
    enable_thinking: bool | None = None


class AnswerBlock(BaseModel):
    type: str
    content: str


class ChatHistoryMessage(BaseModel):
    message_id: str
    role: str
    content_md: str
    created_at: str
    citations: list[Citation] = []


class ChatMessageResponse(BaseModel):
    message_id: str
    answer_md: str
    answer_blocks: list[AnswerBlock]
    citations: list[Citation]
    inference_notes: list[str]
    suggested_followups: list[str]
    recommended_readings: list[RecommendationItem]
    model_used: str | None = None
    debug_info: dict | None = None
