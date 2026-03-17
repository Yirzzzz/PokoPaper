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
            long_term_decision = self.memory_service.build_long_term_write_decision(
                conversation_id=session_id,
                paper_id=None,
                question=question,
                answer=answer["answer_md"],
            )
            recorded_items = self.memory_service.record_long_term_write_decision(long_term_decision)
            debug_info = answer.get("debug_info") or {}
            debug_info["long_term_memory_write_decision"] = long_term_decision
            debug_info["recorded_long_term_memory_items"] = recorded_items
            answer["debug_info"] = debug_info
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
        long_term_decision = self.memory_service.build_long_term_write_decision(
            conversation_id=session_id,
            paper_id=paper_id,
            question=question,
            answer=answer["answer_md"],
        )
        recorded_items = self.memory_service.record_long_term_write_decision(long_term_decision)
        debug_info = answer.get("debug_info") or {}
        debug_info["long_term_memory_write_decision"] = long_term_decision
        debug_info["recorded_long_term_memory_items"] = recorded_items
        answer["debug_info"] = debug_info
        self.short_term_memory.update_short_term_memory(
            session_id,
            question,
            answer["answer_md"],
            selected_model=selected_model,
        )
        return answer
