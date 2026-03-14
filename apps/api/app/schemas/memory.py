from pydantic import BaseModel, Field


class SessionMemoryRecord(BaseModel):
    scope_type: str = "session"
    scope_id: str
    paper_id: str
    recent_questions: list[str] = Field(default_factory=list)
    conversation_summary: str = ""
    recent_turn_summaries: list[str] = Field(default_factory=list)
    active_topics: list[str] = Field(default_factory=list)
    updated_at: str = ""


class PaperLinkItem(BaseModel):
    paper_id: str
    paper_title: str
    relation: str


class CrossPaperLinkItem(BaseModel):
    source_paper_id: str
    target_paper_id: str
    relation: str


class PaperMemoryRecord(BaseModel):
    scope_type: str = "paper"
    scope_id: str
    paper_id: str
    progress_status: str = "new"
    progress_percent: int = 0
    last_read_section: str = "Introduction"
    stuck_points: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    important_takeaways: list[str] = Field(default_factory=list)
    method_summary: str = ""
    experiment_takeaways: list[str] = Field(default_factory=list)
    concepts_seen: list[str] = Field(default_factory=list)
    linked_papers: list[PaperLinkItem] = Field(default_factory=list)


class UserMemoryRecord(BaseModel):
    scope_type: str = "user"
    scope_id: str
    user_id: str
    read_paper_ids: list[str] = Field(default_factory=list)
    preferred_explanation_style: str = "intuitive_then_formula"
    recent_topics: list[str] = Field(default_factory=list)
    paper_link_candidates: list[CrossPaperLinkItem] = Field(default_factory=list)
    weak_concepts: list[str] = Field(default_factory=list)
    mastered_concepts: list[str] = Field(default_factory=list)
    cross_paper_links: list[CrossPaperLinkItem] = Field(default_factory=list)


class MemoryWriteAction(BaseModel):
    target_scope: str
    memory_type: str
    payload: dict = Field(default_factory=dict)
    confidence: float = 0.0


class MemoryWriteDecision(BaseModel):
    should_write: bool
    reason: str | None = None
    writes: list[MemoryWriteAction] = Field(default_factory=list)


class RetrievedMemoryItem(BaseModel):
    source_scope: str
    memory_type: str
    payload: dict = Field(default_factory=dict)
    score: float = 0.0


class MemoryRetrievalResult(BaseModel):
    should_retrieve: bool
    reason: str | None = None
    route: str | None = None
    items: list[RetrievedMemoryItem] = Field(default_factory=list)


class RecalledPaperCandidate(BaseModel):
    paper_id: str
    title: str | None = None
    relation_reason: str
    supporting_memory_ids: list[str] = Field(default_factory=list)
    score: float = 0.0


class CrossPaperRecallResult(BaseModel):
    should_recall: bool
    reason: str | None = None
    candidates: list[RecalledPaperCandidate] = Field(default_factory=list)


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
    important_takeaways: list[str] = []
    method_summary: str = ""
    experiment_takeaways: list[str] = []
    concepts_seen: list[str] = []
    linked_papers: list[PaperLinkItem] = []


class UserMemoryResponse(BaseModel):
    scope_type: str
    scope_id: str
    user_id: str
    read_paper_ids: list[str]
    preferred_explanation_style: str
    recent_topics: list[str]
    paper_link_candidates: list[CrossPaperLinkItem] = []
    weak_concepts: list[str]
    mastered_concepts: list[str] = []
    cross_paper_links: list[CrossPaperLinkItem] = []


class MemoryItem(BaseModel):
    memory_id: str
    scope: str
    scope_type: str
    scope_id: str
    memory_type: str
    payload: dict = Field(default_factory=dict)
    summary: str
    paper_id: str | None = None
    paper_title: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_enabled: bool = True
    write_reason: str | None = None
    write_confidence: float | None = None
    source_question: str | None = None
    source_answer_preview: str | None = None


class MemoryItemListResponse(BaseModel):
    items: list[MemoryItem]
    total: int


class MemoryResetRequest(BaseModel):
    scope: str | None = None
    paper_id: str | None = None
    memory_type: str | None = None


class SessionMemoryMessage(BaseModel):
    message_id: str
    role: str
    content_md: str
    created_at: str


class SessionMemoryView(BaseModel):
    conversation_id: str
    conversation_type: str
    title: str
    paper_id: str | None = None
    paper_title: str | None = None
    created_at: str
    updated_at: str
    is_empty: bool
    recent_questions: list[str] = Field(default_factory=list)
    rolling_summary: str = ""
    recent_messages: list[SessionMemoryMessage] = Field(default_factory=list)
    recent_messages_count: int = 0


class SessionMemoryListResponse(BaseModel):
    items: list[SessionMemoryView]
    total: int


class SessionSummaryRecord(BaseModel):
    summary_text: str = ""
    discussion_topics: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    last_updated_at: str = ""
    covered_message_until: str = ""


class SessionSummaryView(BaseModel):
    conversation_id: str
    conversation_type: str
    title: str
    paper_id: str | None = None
    paper_title: str | None = None
    created_at: str
    updated_at: str
    is_empty: bool
    summary_text: str = ""
    discussion_topics: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    last_updated_at: str = ""
    covered_message_until: str = ""
    pending_messages_count: int = 0


class SessionSummaryListResponse(BaseModel):
    items: list[SessionSummaryView]
    total: int


class PaperEntityMemoryCard(BaseModel):
    paper_id: str
    paper_title: str
    created_at: str
    updated_at: str
    summary_card: str
    motivation: str = ""
    problem: str = ""
    core_proposal: str = ""
    method: str = ""
    value: str = ""
    resolved_gap: str = ""
    test_data: str = ""
    key_results: str = ""
    keywords: list[str] = Field(default_factory=list)


class PaperEntityMemoryListResponse(BaseModel):
    items: list[PaperEntityMemoryCard]
    total: int
