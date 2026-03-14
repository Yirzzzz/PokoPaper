export type PaperCard = {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  status: string;
  progress_percent: number;
  category?: string | null;
  tags?: string[];
};

export type Citation = {
  chunk_id: string;
  section_title: string;
  page_num: number;
  support_level: string;
};

export type Overview = {
  paper_id: string;
  tldr: string;
  research_motivation: string;
  problem_definition: string;
  main_contributions: string[];
  method_summary: string;
  key_modules: Array<{
    name: string;
    purpose: string;
    why_it_matters: string;
  }>;
  key_formulas: Array<{
    formula_id: string;
    latex: string;
    explanation: string;
    variables: Array<{ symbol: string; meaning: string }>;
    citation: Citation;
  }>;
  main_experiments: Array<{
    claim: string;
    evidence: string;
    what_it_proves?: string | null;
    citation: Citation;
  }>;
  limitations: string[];
  prerequisite_knowledge: Array<{ topic: string; reason: string }>;
  conclusion: string;
  transferable_insights: Array<{
    idea: string;
    how_to_apply: string;
  }>;
  recommended_readings: Array<{
    title: string;
    reason: string;
    relation_to_current_paper: string;
    suggested_section: string;
    difficulty_level: string;
  }>;
};

export type ChatResponse = {
  message_id: string;
  answer_md: string;
  answer_blocks: Array<{ type: string; content: string }>;
  citations: Citation[];
  inference_notes: string[];
  suggested_followups: string[];
  model_used: string | null;
  debug_info?: Record<string, unknown> | null;
  recommended_readings: Array<{
    type: string;
    title: string;
    reason: string;
    relation_to_current_paper: string;
    suggested_section: string;
    difficulty_level: string;
  }>;
};

export type ChatHistoryMessage = {
  message_id: string;
  role: "user" | "assistant";
  content_md: string;
  created_at: string;
  citations: Citation[];
};

export type ChatConversation = {
  conversation_id: string;
  session_id: string;
  conversation_type: "global_chat" | "paper_chat";
  paper_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
};

export type ChatModelOption = {
  id: string;
  label: string;
  provider: string;
  model: string;
  base_url: string;
  enabled: boolean;
  supports_thinking: boolean;
};

export type MemoryOverview = {
  read_papers: number;
  weak_concepts: string[];
  preferred_explanation_style: string;
  active_topics: string[];
  recent_stuck_points: Array<{ paper_title: string; concept: string; last_seen_at: string }>;
};

export type CrossPaperLink = {
  source_paper_id: string;
  target_paper_id: string;
  relation: string;
};

export type ReadingMemory = {
  paper_id: string;
  progress_status: string;
  progress_percent: number;
  last_read_section: string;
  stuck_points: string[];
  key_questions: string[];
  important_takeaways?: string[];
  method_summary?: string;
  experiment_takeaways?: string[];
  concepts_seen?: string[];
  linked_papers?: Array<{
    paper_id: string;
    paper_title: string;
    relation: string;
  }>;
};

export type UserEntityMemory = {
  scope_type: "user";
  scope_id: string;
  user_id: string;
  read_paper_ids: string[];
  preferred_explanation_style: string;
  recent_topics: string[];
  paper_link_candidates: CrossPaperLink[];
  weak_concepts: string[];
  mastered_concepts: string[];
  cross_paper_links: CrossPaperLink[];
};

export type PaperEntityMemoryCard = {
  paper_id: string;
  paper_title: string;
  created_at: string;
  updated_at: string;
  summary_card: string;
  motivation: string;
  problem: string;
  core_proposal: string;
  method: string;
  value: string;
  resolved_gap: string;
  test_data: string;
  key_results: string;
  keywords: string[];
};

export type PaperEntityMemoryListResponse = {
  items: PaperEntityMemoryCard[];
  total: number;
};

export type MemoryItem = {
  memory_id: string;
  scope: string;
  scope_type: "session" | "paper" | "user";
  scope_id: string;
  memory_type: string;
  payload: Record<string, unknown>;
  summary: string;
  paper_id?: string | null;
  paper_title?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  is_enabled: boolean;
  write_reason?: string | null;
  write_confidence?: number | null;
  source_question?: string | null;
  source_answer_preview?: string | null;
};

export type MemoryItemListResponse = {
  items: MemoryItem[];
  total: number;
};

export type SessionMemoryMessage = {
  message_id: string;
  role: "user" | "assistant";
  content_md: string;
  created_at: string;
};

export type SessionMemoryView = {
  conversation_id: string;
  conversation_type: "global_chat" | "paper_chat";
  title: string;
  paper_id: string | null;
  paper_title?: string | null;
  created_at: string;
  updated_at: string;
  is_empty: boolean;
  recent_questions: string[];
  rolling_summary: string;
  recent_messages: SessionMemoryMessage[];
  recent_messages_count: number;
};

export type SessionMemoryListResponse = {
  items: SessionMemoryView[];
  total: number;
};

export type SessionSummaryView = {
  conversation_id: string;
  conversation_type: "global_chat" | "paper_chat";
  title: string;
  paper_id: string | null;
  paper_title?: string | null;
  created_at: string;
  updated_at: string;
  is_empty: boolean;
  summary_text: string;
  discussion_topics: string[];
  key_points: string[];
  open_questions: string[];
  last_updated_at: string;
  covered_message_until: string;
  pending_messages_count: number;
};

export type SessionSummaryListResponse = {
  items: SessionSummaryView[];
  total: number;
};
