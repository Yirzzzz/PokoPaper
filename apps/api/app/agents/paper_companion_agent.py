from app.services.memory.service import MemoryService
from app.services.rag.service import RAGService
from app.services.recommendations.service import RecommendationService
from app.services.short_term_memory import ShortTermMemoryService


class PaperCompanionAgent:
    def __init__(self) -> None:
        self.memory_service = MemoryService()
        self.rag_service = RAGService()
        self.recommendation_service = RecommendationService()
        self.short_term_memory = ShortTermMemoryService()

    def answer(
        self,
        paper_id: str | None,
        session_id: str,
        question: str,
        selected_model: str | None = None,
        enable_thinking: bool | None = None,
    ) -> dict:
        if paper_id is None:
            answer = self.rag_service.answer_global_question(
                question=question,
                conversation_id=session_id,
                selected_model=selected_model,
                enable_thinking=enable_thinking,
            )
            self.memory_service.update_user_memory_from_conversation(
                paper_id=None,
                question=question,
                answer=answer["answer_md"],
                overview=None,
            )
            self.short_term_memory.update_short_term_memory(
                session_id,
                question,
                answer["answer_md"],
                selected_model=selected_model,
            )
            return answer

        answer = self.rag_service.answer_question(
            paper_id=paper_id,
            question=question,
            conversation_id=session_id,
            selected_model=selected_model,
            enable_thinking=enable_thinking,
        )
        self.memory_service.update_user_memory_from_conversation(
            paper_id=paper_id,
            question=question,
            answer=answer["answer_md"],
            overview=answer.get("overview"),
        )
        self.short_term_memory.update_short_term_memory(
            session_id,
            question,
            answer["answer_md"],
            selected_model=selected_model,
        )
        return answer
