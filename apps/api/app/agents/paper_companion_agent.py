from app.services.memory.service import MemoryService
from app.services.rag.service import RAGService
from app.services.recommendations.service import RecommendationService


class PaperCompanionAgent:
    def __init__(self) -> None:
        self.rag_service = RAGService()
        self.memory_service = MemoryService()
        self.recommendation_service = RecommendationService()

    def answer(
        self,
        paper_id: str,
        question: str,
        selected_model: str | None = None,
        enable_thinking: bool | None = None,
    ) -> dict:
        # TODO: replace with actual tool selection and prompt orchestration.
        memory = self.memory_service.get_paper_memory(paper_id=paper_id)
        answer = self.rag_service.answer_question(
            paper_id=paper_id,
            question=question,
            selected_model=selected_model,
            memory=memory,
            enable_thinking=enable_thinking,
        )
        if memory["progress_percent"] < 60:
            answer["answer_blocks"].append(
                {
                    "type": "memory_hint",
                    "content": f"你上次读到 {memory['last_read_section']}，可以先回顾这一节再看当前问题。",
                }
            )
        self.memory_service.update_conversation_memory(
            paper_id=paper_id,
            question=question,
            answer=answer["answer_md"],
        )
        return answer
