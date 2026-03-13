from __future__ import annotations

from typing import Any


def generate_overview(
    paper_id: str,
    title: str,
    abstract: str,
    sections: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    intro = chunks[0]["content"] if chunks else abstract
    method_chunk = next(
        (chunk for chunk in chunks if chunk["chunk_type"] in {"formula", "paragraph"} and "method" in chunk["section_title"].lower()),
        chunks[0] if chunks else None,
    )
    experiment_chunk = next(
        (chunk for chunk in chunks if chunk["chunk_type"] == "experiment_finding"),
        chunks[-1] if chunks else None,
    )
    formula_citation = (
        {
            "chunk_id": method_chunk["chunk_id"],
            "section_title": method_chunk["section_title"],
            "page_num": method_chunk["page_num"],
            "support_level": "explicit",
        }
        if method_chunk
        else {
            "chunk_id": "chunk-0",
            "section_title": "Unknown",
            "page_num": 1,
            "support_level": "explicit",
        }
    )
    experiment_citation = (
        {
            "chunk_id": experiment_chunk["chunk_id"],
            "section_title": experiment_chunk["section_title"],
            "page_num": experiment_chunk["page_num"],
            "support_level": "explicit",
        }
        if experiment_chunk
        else formula_citation
    )
    return {
        "paper_id": paper_id,
        "tldr": abstract[:300] if abstract else f"{title} focuses on helping readers understand the paper through structured guidance.",
        "research_motivation": intro[:500] if intro else "This paper is motivated by the need for more accessible paper understanding.",
        "problem_definition": f"{title} aims to make paper reading easier by turning paper structure into grounded, explainable assistance.",
        "main_contributions": [
            "Parses a paper into structured sections and chunks for guided reading.",
            "Builds an overview that highlights motivation, method, and experiments.",
            "Supports citation-aware QA over the parsed paper content.",
        ],
        "method_summary": method_chunk["content"][:600] if method_chunk else abstract[:500],
        "key_modules": [
            {
                "name": "Typed chunk routing",
                "purpose": "根据问题类型优先选择更合适的论文片段进行分析。",
                "why_it_matters": "它决定了系统回答时看到的是方法证据还是实验证据。",
            }
        ],
        "key_formulas": [
            {
                "formula_id": "formula-generated-1",
                "latex": "S(q, c) = \\alpha \\cdot rel(q, c) + \\beta \\cdot route(q, c)",
                "explanation": "A placeholder routing score is used in the MVP to show how question intent can influence retrieval preference.",
                "variables": [
                    {"symbol": "q", "meaning": "user question"},
                    {"symbol": "c", "meaning": "candidate chunk"},
                    {"symbol": "\\alpha, \\beta", "meaning": "retrieval weights"},
                ],
                "citation": formula_citation,
            }
        ],
        "main_experiments": [
            {
                "claim": "The paper includes an experiment-focused validation section.",
                "evidence": experiment_chunk["content"][:500] if experiment_chunk else "No dedicated experiment chunk was extracted; this is a fallback summary.",
                "what_it_proves": "论文中的关键设计是否真的带来效果提升。",
                "citation": experiment_citation,
            }
        ],
        "limitations": [
            "Current parser uses heuristic section detection.",
            "Formula and table extraction are placeholder implementations in this version.",
        ],
        "prerequisite_knowledge": [
            {"topic": "RAG basics", "reason": "Helpful for understanding retrieval-grounded question answering."},
            {"topic": "Paper structure literacy", "reason": "Knowing intro, method, and experiment roles improves reading speed."},
        ],
        "conclusion": "This paper shows how a companion-style interface can turn raw paper text into guided understanding.",
        "transferable_insights": [
            {
                "idea": "问题类型感知的检索或分析路径",
                "how_to_apply": "可以迁移到法律文档、医学文献、技术文档问答中，按问题类型选择不同证据来源。",
            }
        ],
        "recommended_readings": [
            {
                "title": "RAG Foundations",
                "reason": "帮助理解检索增强生成的基本范式。",
                "relation_to_current_paper": "提供当前系统的底层方法背景。",
                "suggested_section": "Introduction",
                "difficulty_level": "beginner",
            }
        ],
        "chunks": chunks,
        "sections": sections,
    }
