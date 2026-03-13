from __future__ import annotations

import logging
from uuid import uuid4

from app.repositories.factory import get_repository
from app.services.llm.service import LLMService

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self) -> None:
        self.repo = get_repository()
        self.llm_service = LLMService()

    def get_overview(self, paper_id: str) -> dict:
        overview = self.repo.get_overview(paper_id)
        if overview is None:
            raise KeyError(f"overview not found: {paper_id}")
        return self._normalize_overview(overview)

    def answer_question(
        self,
        paper_id: str,
        question: str,
        selected_model: str | None = None,
        memory: dict | None = None,
        enable_thinking: bool | None = None,
    ) -> dict:
        overview = self.get_overview(paper_id)
        chunks = overview.get("chunks", [])
        lower_question = question.lower()
        intent = self._infer_intent(lower_question)
        preferred = self._select_evidence_chunks(chunks=chunks, lower_question=lower_question, intent=intent)
        citations = [
            {
                "chunk_id": chunk["chunk_id"],
                "section_title": chunk["section_title"],
                "page_num": chunk["page_num"],
                "support_level": "explicit",
            }
            for chunk in preferred[:2]
        ]
        evidence_text = "\n\n".join(chunk["content"][:280] for chunk in preferred[:3]) or overview["tldr"]
        llm_answer = None
        model_config = self.llm_service.get_model_config(selected_model)
        if model_config is not None:
            llm_answer = self.llm_service.generate_grounded_answer(
                selected_model=selected_model,
                question=question,
                overview=overview,
                evidence_chunks=preferred,
                memory=memory or {"preferred_explanation_style": "intuitive_then_formula"},
                enable_thinking=enable_thinking,
            )
        logger.info(
            "chat.answer: paper_id=%s model=%s source=%s",
            paper_id,
            model_config["model"] if model_config else "none",
            "llm" if llm_answer else "heuristic_fallback",
        )
        debug_info = self.llm_service.last_debug_info
        llm_succeeded = bool(llm_answer) and bool(debug_info) and debug_info.get("status") == "success"
        background_tip = (
            "如果你对相关公式背景不熟，建议先补对应数学概念，再看这部分方法。"
            if intent == "formula"
            else "如果你还不熟悉 ablation study，可以先理解它为什么用来验证每个模块的必要性。"
        )
        return {
            "message_id": f"message-{uuid4().hex[:8]}",
            "answer_md": llm_answer
            or (
                self._build_fallback_answer(
                    question=question,
                    intent=intent,
                    overview=overview,
                    evidence_text=evidence_text,
                    preferred=preferred,
                )
            ),
            "answer_blocks": [
                {
                    "type": "direct_answer",
                    "content": self._build_direct_answer(intent=intent, overview=overview, preferred=preferred),
                },
                {"type": "background_tip", "content": background_tip},
            ],
            "citations": citations,
            "inference_notes": [
                "回答中的高层总结经过了结构化概览压缩，不等于论文原文逐句复述。"
            ],
            "suggested_followups": [
                "这个 routing score 怎么计算？",
                "实验里如何证明 memory 有用？",
            ],
            "recommended_readings": [
                {
                    "type": "prerequisite",
                    "title": item["title"],
                    "reason": item["reason"],
                    "relation_to_current_paper": item["relation_to_current_paper"],
                    "suggested_section": item["suggested_section"],
                    "difficulty_level": item["difficulty_level"],
                }
                for item in overview.get("recommended_readings", [])[:3]
            ],
            "model_used": model_config["label"] if llm_succeeded and model_config else "heuristic-fallback",
            "debug_info": debug_info,
        }

    @staticmethod
    def _infer_intent(lower_question: str) -> str:
        if any(keyword in lower_question for keyword in ["实验", "ablation", "result", "baseline", "对比"]):
            return "experiment"
        if any(keyword in lower_question for keyword in ["公式", "equation", "loss", "证明", "变量"]):
            return "formula"
        if any(keyword in lower_question for keyword in ["方法", "模块", "设计", "为什么这样设计", "架构"]):
            return "method"
        if any(keyword in lower_question for keyword in ["动机", "贡献", "解决什么问题", "做了什么"]):
            return "motivation"
        if any(keyword in lower_question for keyword in ["先补", "背景", "推荐", "阅读"]):
            return "reading"
        return "general"

    @staticmethod
    def _select_evidence_chunks(chunks: list[dict], lower_question: str, intent: str) -> list[dict]:
        if not chunks:
            return []
        scored: list[tuple[int, dict]] = []
        for chunk in chunks:
            score = 0
            chunk_type = chunk.get("chunk_type", "")
            section_title = chunk.get("section_title", "").lower()
            content = chunk.get("content", "").lower()
            if intent == "experiment":
                if chunk_type == "experiment_finding":
                    score += 6
                if "experiment" in section_title or "result" in section_title:
                    score += 4
            elif intent == "formula":
                if chunk_type == "formula":
                    score += 6
                if "method" in section_title or "equation" in content or "loss" in content:
                    score += 4
            elif intent == "method":
                if "method" in section_title:
                    score += 5
                if chunk_type in {"paragraph", "formula"}:
                    score += 3
            elif intent == "motivation":
                if "introduction" in section_title or "intro" in section_title:
                    score += 5
            elif intent == "reading":
                if "conclusion" in section_title or "discussion" in section_title:
                    score += 4
            for keyword in lower_question.split():
                if keyword and keyword in content:
                    score += 1
            scored.append((score, chunk))
        ranked = [item for _, item in sorted(scored, key=lambda item: item[0], reverse=True)]
        top = [chunk for chunk in ranked[:3] if chunk]
        return top or chunks[:3]

    @staticmethod
    def _build_direct_answer(intent: str, overview: dict, preferred: list[dict]) -> str:
        if intent == "experiment":
            return overview.get("main_experiments", [{}])[0].get("what_it_proves", overview["tldr"])
        if intent == "formula":
            return overview.get("key_formulas", [{}])[0].get("explanation", overview["tldr"])
        if intent == "method":
            return overview.get("method_summary", overview["tldr"])
        if intent == "motivation":
            return overview.get("research_motivation", overview["tldr"])
        if intent == "reading":
            return overview.get("prerequisite_knowledge", [{}])[0].get("reason", overview["tldr"])
        return preferred[0]["content"][:180] if preferred else overview["tldr"]

    @staticmethod
    def _build_fallback_answer(
        question: str,
        intent: str,
        overview: dict,
        evidence_text: str,
        preferred: list[dict],
    ) -> str:
        if intent == "experiment":
            experiment = overview.get("main_experiments", [{}])[0]
            return (
                f"针对你的问题，当前最相关的实验结论是：{experiment.get('claim', '实验部分展示了方法效果。')}\n\n"
                f"它主要证明了：{experiment.get('what_it_proves', '论文中的关键设计是有效的。')}\n\n"
                f"相关证据摘要：{evidence_text}"
            )
        if intent == "formula":
            formula = overview.get("key_formulas", [{}])[0]
            return (
                f"针对这个公式，直观上它想表达的是：{formula.get('explanation', '该公式描述了问题与证据之间的关系。')}\n\n"
                f"相关证据摘要：{evidence_text}"
            )
        if intent == "method":
            return (
                f"针对你的问题，这篇论文的方法主线是：{overview.get('method_summary', overview['tldr'])[:320]}\n\n"
                f"相关证据摘要：{evidence_text}"
            )
        if intent == "motivation":
            return (
                f"这篇论文的核心动机是：{overview.get('research_motivation', overview['tldr'])[:260]}\n\n"
                f"相关证据摘要：{evidence_text}"
            )
        if intent == "reading":
            prereq = overview.get("prerequisite_knowledge", [])
            recommendation = prereq[0]["topic"] if prereq else "相关背景知识"
            reason = prereq[0]["reason"] if prereq else "有助于理解论文内容。"
            return f"如果你当前觉得难，建议先补 `{recommendation}`。原因是：{reason}"
        return (
            f"围绕你的问题，当前最相关的证据是：\n\n{evidence_text}\n\n"
            f"如果把它压缩成一句话，可以理解为：{preferred[0]['content'][:220] if preferred else overview['tldr']}"
        )

    @staticmethod
    def _normalize_overview(overview: dict) -> dict:
        normalized = dict(overview)
        normalized.setdefault(
            "key_modules",
            [
                {
                    "name": "Core method",
                    "purpose": "该模块承载论文的主要方法设计。",
                    "why_it_matters": "它通常决定了方法相对 baseline 的核心改进点。",
                }
            ],
        )
        normalized.setdefault("conclusion", normalized.get("tldr", "This paper presents a structured research contribution."))
        normalized.setdefault(
            "transferable_insights",
            [
                {
                    "idea": "将论文方法拆成模块理解",
                    "how_to_apply": "可迁移到其他论文阅读、系统设计和实验分析任务中。",
                }
            ],
        )
        normalized.setdefault(
            "recommended_readings",
            [
                {
                    "title": "Background Reading",
                    "reason": "补足当前论文相关的基础背景知识。",
                    "relation_to_current_paper": "帮助理解本文方法和实验设置。",
                    "suggested_section": "Introduction",
                    "difficulty_level": "beginner",
                }
            ],
        )
        normalized["main_experiments"] = [
            {
                **item,
                "what_it_proves": item.get("what_it_proves", "该实验用于验证论文中的关键设计是否有效。"),
            }
            for item in normalized.get("main_experiments", [])
        ]
        return normalized
