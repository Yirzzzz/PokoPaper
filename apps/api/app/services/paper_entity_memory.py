from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.factory import get_repository
from app.schemas.memory import PaperEntityMemoryCard


class PaperEntityMemoryService:
    def __init__(self) -> None:
        self.repo = get_repository()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _clean_text(value: str | None, fallback: str = "") -> str:
        return (value or fallback).strip()

    @staticmethod
    def _join_lines(values: list[str], limit: int = 3) -> str:
        cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        return "；".join(cleaned[:limit])

    @staticmethod
    def _extract_keywords(overview: dict) -> list[str]:
        keywords: list[str] = []
        for item in overview.get("prerequisite_knowledge", [])[:4]:
            topic = (item.get("topic") or "").strip()
            if topic and topic not in keywords:
                keywords.append(topic)
        for item in overview.get("key_modules", [])[:4]:
            name = (item.get("name") or "").strip()
            if name and name not in keywords:
                keywords.append(name)
        return keywords[:8]

    def build_card(self, paper_id: str, paper_title: str, overview: dict, created_at: str = "", updated_at: str = "") -> dict:
        motivation = self._clean_text(overview.get("research_motivation"), "当前版本未提取到明确动机。")
        problem = self._clean_text(overview.get("problem_definition"), "当前版本未提取到明确问题定义。")
        core_proposal = self._join_lines(overview.get("main_contributions", []), limit=3) or self._clean_text(
            overview.get("tldr"),
            "当前版本未提取到明确核心贡献。",
        )
        method = self._clean_text(overview.get("method_summary"), "当前版本未提取到明确方法主线。")
        value = self._join_lines(
            [item.get("idea", "") for item in overview.get("transferable_insights", [])],
            limit=2,
        ) or self._clean_text(overview.get("conclusion"), "当前版本未提取到明确价值总结。")
        resolved_gap = self._join_lines(
            [
                self._clean_text(overview.get("problem_definition")),
                self._join_lines(overview.get("main_contributions", []), limit=2),
            ],
            limit=2,
        ) or problem
        experiments = overview.get("main_experiments", [])
        test_data = self._join_lines(
            [item.get("evidence", "") for item in experiments],
            limit=2,
        ) or "当前版本未提取到明确测试数据描述。"
        key_results = self._join_lines(
            [
                item.get("claim", "") or item.get("what_it_proves", "")
                for item in experiments
            ],
            limit=2,
        ) or "当前版本未提取到明确实验结果。"
        summary_card = (
            f"{paper_title} 的核心脉络是：此前工作的主要不足或背景动机在于 {motivation}。"
            f" 这篇论文要解决的问题是 {problem}。"
            f" 它主要提出了 {core_proposal}，方法主线是 {method}。"
            f" 这项工作的价值在于 {value}，它补上的关键空缺可以概括为 {resolved_gap}。"
            f" 在实验与测试部分，重点证据包括 {test_data}，关键结果是 {key_results}。"
        )
        card = PaperEntityMemoryCard(
            paper_id=paper_id,
            paper_title=paper_title,
            created_at=created_at or self._now(),
            updated_at=updated_at or self._now(),
            summary_card=summary_card,
            motivation=motivation,
            problem=problem,
            core_proposal=core_proposal,
            method=method,
            value=value,
            resolved_gap=resolved_gap,
            test_data=test_data,
            key_results=key_results,
            keywords=self._extract_keywords(overview),
        )
        return card.model_dump()

    def upsert_from_overview(self, paper_id: str, overview: dict) -> dict:
        paper = self.repo.get_paper(paper_id)
        if paper is None:
            raise KeyError(f"paper not found: {paper_id}")
        existing = self.repo.get_paper_entity_card(paper_id) if hasattr(self.repo, "get_paper_entity_card") else None
        card = self.build_card(
            paper_id=paper_id,
            paper_title=paper.get("title", paper_id),
            overview=overview,
            created_at=(existing or {}).get("created_at", paper.get("created_at", self._now())),
            updated_at=paper.get("updated_at", self._now()),
        )
        self.repo.save_paper_entity_card(paper_id, card)
        return card

    def get_card(self, paper_id: str) -> dict:
        card = self.repo.get_paper_entity_card(paper_id)
        if card is None:
            raise KeyError(f"paper entity memory card not found: {paper_id}")
        return card

    def list_cards(self) -> list[dict]:
        return self.repo.list_paper_entity_cards()
