from __future__ import annotations

from uuid import uuid4


PAPER_ID = "paper-demo-001"
SESSION_ID = "session-demo-001"

MOCK_PAPERS = [
    {
        "id": PAPER_ID,
        "title": "PokeRAG: Retrieval-Augmented Companions for Beginner Paper Reading",
        "authors": ["Pallet Oak", "Misty Waterflower"],
        "abstract": "A teaching-oriented paper companion system that grounds answers with citations and adapts explanations using memory.",
        "status": "ready",
        "progress_percent": 48,
    }
]

MOCK_STRUCTURE = {
    "paper_id": PAPER_ID,
    "sections": [
        {"section_title": "1 Introduction", "section_path": "Introduction", "page_start": 1, "page_end": 2},
        {"section_title": "2 Method", "section_path": "Method", "page_start": 3, "page_end": 5},
        {"section_title": "3 Experiments", "section_path": "Experiments", "page_start": 6, "page_end": 8},
        {"section_title": "4 Limitations", "section_path": "Limitations", "page_start": 9, "page_end": 9},
    ],
    "formulas_count": 2,
    "tables_count": 2,
    "figures_count": 1,
}

MOCK_OVERVIEW = {
    "paper_id": PAPER_ID,
    "tldr": "This paper builds a paper-reading agent that combines RAG, grounded citations, and user memory to help beginners understand research papers faster.",
    "research_motivation": "Beginner readers often get lost because paper summaries are too shallow and PDF chat tools lack pedagogical adaptation.",
    "problem_definition": "The paper targets interactive paper understanding with grounded evidence, background-aware explanations, and long-term reading memory.",
    "main_contributions": [
        "Defines the paper companion task beyond plain PDF QA.",
        "Introduces intent-aware retrieval over multiple chunk types.",
        "Uses reading memory to personalize explanation depth and prerequisite recommendations.",
    ],
    "method_summary": "The system parses papers into typed chunks, routes questions by intent, retrieves grounded evidence, and synthesizes answers with explicit citations and background tips.",
    "key_formulas": [
        {
            "formula_id": "formula-1",
            "latex": "S(q, c) = \\alpha \\cdot \\mathrm{Dense}(q, c) + \\beta \\cdot \\mathrm{TypeMatch}(q, c)",
            "explanation": "The score combines semantic relevance and chunk-type compatibility, so method questions prefer method chunks and experiment questions prefer results chunks.",
            "variables": [
                {"symbol": "q", "meaning": "user question"},
                {"symbol": "c", "meaning": "candidate chunk"},
                {"symbol": "\\alpha, \\beta", "meaning": "routing weights"},
            ],
            "citation": {
                "chunk_id": "chunk-method-2",
                "section_title": "2 Method",
                "page_num": 4,
                "support_level": "explicit",
            },
        }
    ],
    "main_experiments": [
        {
            "claim": "Memory-aware explanations reduced follow-up clarification requests.",
            "evidence": "Users needed fewer background questions when the system injected prerequisite guidance before detailed answers.",
            "citation": {
                "chunk_id": "chunk-exp-1",
                "section_title": "3 Experiments",
                "page_num": 7,
                "support_level": "explicit",
            },
        }
    ],
    "limitations": [
        "The recommendation quality still depends on the available reading graph.",
        "Formula extraction is weaker on scanned PDFs.",
    ],
    "prerequisite_knowledge": [
        {"topic": "RAG basics", "reason": "The method assumes dense retrieval and grounded generation."},
        {"topic": "Transformer attention", "reason": "Several baseline comparisons rely on encoder-decoder retrieval settings."},
    ],
}

MOCK_MEMORY = {
    "overview": {
        "read_papers": 6,
        "weak_concepts": ["ablation study", "contrastive loss"],
        "preferred_explanation_style": "intuitive_then_formula",
        "active_topics": ["RAG", "paper agents", "LLM memory"],
        "recent_stuck_points": [
            {"paper_title": "PokeRAG", "concept": "retrieval routing", "last_seen_at": "2026-03-12T10:00:00Z"}
        ],
    },
    "paper": {
        "paper_id": PAPER_ID,
        "progress_status": "reading",
        "progress_percent": 48,
        "last_read_section": "2 Method",
        "stuck_points": ["why chunk types matter", "how citations are grounded"],
        "key_questions": ["What does the routing score mean?", "Why not use plain top-k vector retrieval?"],
    },
}


def build_upload_result() -> dict[str, str]:
    suffix = uuid4().hex[:8]
    return {
        "paper_id": f"paper-{suffix}",
        "job_id": f"job-{suffix}",
        "status": "queued",
    }
