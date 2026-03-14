from pydantic import BaseModel

from app.schemas.common import Citation, RecommendationItem


class ConversationType:
    GLOBAL_CHAT = "global_chat"
    PAPER_CHAT = "paper_chat"


class CreateChatSessionRequest(BaseModel):
    paper_id: str


class CreateChatSessionResponse(BaseModel):
    conversation_id: str
    session_id: str
    conversation_type: str
    paper_id: str | None = None
    title: str
    created_at: str
    updated_at: str
    is_deleted: bool = False


class CreateGlobalConversationRequest(BaseModel):
    title: str | None = None


class ListConversationsResponse(BaseModel):
    conversations: list[CreateChatSessionResponse]


class ChatMessageRequest(BaseModel):
    paper_id: str | None = None
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
