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

export type ReadingMemory = {
  paper_id: string;
  progress_status: string;
  progress_percent: number;
  last_read_section: string;
  stuck_points: string[];
  key_questions: string[];
};
