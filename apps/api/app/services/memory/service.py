from app.repositories.factory import get_repository


class MemoryService:
    def __init__(self) -> None:
        self.repo = get_repository()

    @staticmethod
    def _is_meaningful_topic(value: str | None) -> bool:
        if not value:
            return False
        normalized = value.strip().lower()
        return normalized not in {"", "unknown", "unknown author", "未设系别", "none", "null"}

    def _collect_active_topics(self, papers: list[dict]) -> list[str]:
        topic_counts: dict[str, int] = {}
        topic_display: dict[str, str] = {}

        for paper in papers:
            candidates = [paper.get("category"), *(paper.get("tags") or [])]
            for candidate in candidates:
                if not isinstance(candidate, str) or not self._is_meaningful_topic(candidate):
                    continue
                normalized = candidate.strip().lower()
                topic_counts[normalized] = topic_counts.get(normalized, 0) + 1
                topic_display.setdefault(normalized, candidate.strip())

        ranked = sorted(
            topic_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        return [topic_display[key] for key, _ in ranked[:6]]

    def get_overview(self) -> dict:
        papers = self.repo.list_papers()
        memories = [self.repo.get_memory(paper["id"]) for paper in papers]
        weak_concepts: list[str] = []
        for memory in memories:
            if not memory:
                continue
            weak_concepts.extend(memory.get("stuck_points", []))
        weak_concepts = weak_concepts[:6]
        active_topics = self._collect_active_topics(papers)

        return {
            "read_papers": len(papers),
            "weak_concepts": weak_concepts or ["retrieval routing", "formula interpretation"],
            "preferred_explanation_style": "intuitive_then_formula",
            "active_topics": active_topics,
            "recent_stuck_points": [
                {
                    "paper_title": paper["title"],
                    "concept": (
                        ((self.repo.get_memory(paper["id"]) or {}).get("stuck_points") or ["overview grounding"])[0]
                    ),
                    "last_seen_at": paper["updated_at"],
                }
                for paper in papers[:3]
            ],
        }

    def get_paper_memory(self, paper_id: str) -> dict:
        memory = self.repo.get_memory(paper_id)
        if memory is None:
            return {
                "paper_id": paper_id,
                "progress_status": "new",
                "progress_percent": 0,
                "last_read_section": "Introduction",
                "stuck_points": [],
                "key_questions": [],
                "conversation_summary": "",
                "recent_questions": [],
            }
        return memory

    def update_conversation_memory(self, paper_id: str, question: str, answer: str) -> dict:
        memory = self.get_paper_memory(paper_id)
        recent_questions = [*memory.get("recent_questions", []), question][-8:]
        prior_summary = memory.get("conversation_summary", "")
        answer_preview = " ".join(answer.split())[:240]
        if prior_summary:
            summary = f"{prior_summary}\n- Q: {question}\n- A: {answer_preview}"
        else:
            summary = f"- Q: {question}\n- A: {answer_preview}"
        memory["conversation_summary"] = summary[-4000:]
        memory["recent_questions"] = recent_questions
        if question not in memory.get("key_questions", []):
            memory["key_questions"] = [*memory.get("key_questions", []), question][-8:]
        self.repo.save_memory(paper_id, memory)
        return memory
