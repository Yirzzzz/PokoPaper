import tempfile
import unittest
from uuid import uuid4

from app.core.config import settings
from app.repositories.local_store import LocalStoreRepository
from app.schemas.chat import ConversationType
from app.agents.prompts.paper_analysis_prompt import (
    build_agent_answer_prompt,
    build_global_agent_answer_prompt,
)
from app.agents.paper_companion_agent import PaperCompanionAgent
from app.services.rag.service import RAGService
from app.services.memory.service import MemoryService
from app.services.paper_entity_memory import PaperEntityMemoryService
from app.services.short_term_memory import ShortTermMemoryService


class StableChatModeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_storage_dir = settings.storage_dir
        self.previous_use_mock = settings.use_mock_services
        settings.storage_dir = self.temp_dir.name
        settings.use_mock_services = True

    def tearDown(self) -> None:
        settings.storage_dir = self.previous_storage_dir
        settings.use_mock_services = self.previous_use_mock
        self.temp_dir.cleanup()

    @staticmethod
    def _save_test_overview(repo: LocalStoreRepository, paper_id: str) -> None:
        repo.save_overview(
            paper_id,
            {
                "paper_id": paper_id,
                "tldr": "Test overview",
                "research_motivation": "Test motivation",
                "problem_definition": "Test problem",
                "main_contributions": ["Test contribution"],
                "method_summary": "Test method",
                "key_modules": [],
                "key_formulas": [],
                "main_experiments": [],
                "limitations": [],
                "prerequisite_knowledge": [],
                "conclusion": "Test conclusion",
                "transferable_insights": [],
                "recommended_readings": [],
                "chunks": [
                    {
                        "chunk_id": "chunk-1",
                        "section_title": "Method",
                        "page_num": 1,
                        "chunk_type": "paragraph",
                        "content": "Test method detail",
                    }
                ],
            },
        )

    @staticmethod
    def _append_user_message(
        repo: LocalStoreRepository,
        conversation_id: str,
        turn_index: int,
        question: str,
    ) -> None:
        base_minute = turn_index * 2
        repo.create_chat_message(
            {
                "message_id": f"{conversation_id}-user-{turn_index}",
                "session_id": conversation_id,
                "role": "user",
                "content_md": question,
                "citations": [],
                "created_at": f"2026-03-14T00:{base_minute:02d}:00+00:00",
            }
        )

    @staticmethod
    def _append_assistant_message(
        repo: LocalStoreRepository,
        conversation_id: str,
        turn_index: int,
        answer: str,
    ) -> None:
        base_minute = turn_index * 2
        repo.create_chat_message(
            {
                "message_id": f"{conversation_id}-assistant-{turn_index}",
                "session_id": conversation_id,
                "role": "assistant",
                "content_md": answer,
                "citations": [],
                "created_at": f"2026-03-14T00:{base_minute + 1:02d}:00+00:00",
            }
        )

    def test_global_chat_supports_multiple_create_switch_and_delete(self) -> None:
        repo = LocalStoreRepository()
        first = repo.create_chat_session(
            {
                "session_id": "session-global-a",
                "conversation_id": "session-global-a",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Global A",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        second = repo.create_chat_session(
            {
                "session_id": "session-global-b",
                "conversation_id": "session-global-b",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Global B",
                "created_at": "2026-03-14T00:00:01+00:00",
                "updated_at": "2026-03-14T00:00:01+00:00",
            }
        )

        listed = repo.list_global_chat_sessions()
        repo.delete_global_chat_session(first["session_id"])
        remaining = repo.list_global_chat_sessions()

        self.assertEqual([item["session_id"] for item in listed], [second["session_id"], first["session_id"]])
        self.assertEqual([item["session_id"] for item in remaining], [second["session_id"]])
        self.assertIsNone(repo.get_chat_session(first["session_id"]))

    def test_each_paper_has_only_one_fixed_paper_chat_conversation(self) -> None:
        repo = LocalStoreRepository()
        created = repo.create_chat_session(
            {
                "session_id": "session-paper-a",
                "conversation_id": "session-paper-a",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-a",
                "title": "Paper A",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_session(
            {
                "session_id": "session-paper-a-duplicate",
                "conversation_id": "session-paper-a-duplicate",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-a",
                "title": "Paper A Duplicate",
                "created_at": "2026-03-14T00:00:01+00:00",
                "updated_at": "2026-03-14T00:00:01+00:00",
            }
        )

        resolved = repo.get_chat_session_by_paper("paper-a")

        self.assertEqual(resolved["session_id"], created["session_id"])

    def test_global_chat_and_paper_chat_are_strictly_isolated(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-global",
                "conversation_id": "session-global",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Global",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_session(
            {
                "session_id": "session-paper",
                "conversation_id": "session-paper",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-a",
                "title": "Paper",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m1",
                "session_id": "session-global",
                "role": "user",
                "content_md": "global message",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m2",
                "session_id": "session-paper",
                "role": "user",
                "content_md": "paper message",
                "citations": [],
                "created_at": "2026-03-14T00:00:01+00:00",
            }
        )

        self.assertEqual([item["content_md"] for item in repo.list_chat_messages("session-global")], ["global message"])
        self.assertEqual([item["content_md"] for item in repo.list_chat_messages("session-paper")], ["paper message"])

    def test_different_paper_chats_are_strictly_isolated(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-paper-a",
                "conversation_id": "session-paper-a",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-a",
                "title": "Paper A",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_session(
            {
                "session_id": "session-paper-b",
                "conversation_id": "session-paper-b",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-b",
                "title": "Paper B",
                "created_at": "2026-03-14T00:00:01+00:00",
                "updated_at": "2026-03-14T00:00:01+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m1",
                "session_id": "session-paper-a",
                "role": "user",
                "content_md": "paper a only",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m2",
                "session_id": "session-paper-b",
                "role": "user",
                "content_md": "paper b only",
                "citations": [],
                "created_at": "2026-03-14T00:00:01+00:00",
            }
        )

        self.assertEqual([item["content_md"] for item in repo.list_chat_messages("session-paper-a")], ["paper a only"])
        self.assertEqual([item["content_md"] for item in repo.list_chat_messages("session-paper-b")], ["paper b only"])

    def test_uploading_new_paper_does_not_reset_existing_global_chat(self) -> None:
        repo = LocalStoreRepository()
        global_session = {
            "session_id": f"session-{uuid4().hex[:8]}",
            "conversation_type": ConversationType.GLOBAL_CHAT,
            "paper_id": None,
            "title": "Global Session",
            "created_at": "2026-03-14T00:00:00+00:00",
            "updated_at": "2026-03-14T00:00:00+00:00",
        }
        global_session["conversation_id"] = global_session["session_id"]
        repo.create_chat_session(global_session)
        repo.upsert_paper(
            {
                "id": "paper-new",
                "title": "New Paper",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 10,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )

        listed = repo.list_global_chat_sessions()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["session_id"], global_session["session_id"])

    def test_answer_prompts_include_short_term_context_without_classification_prompt(self) -> None:
        prompt = build_agent_answer_prompt(
            question="这篇论文的方法是什么？",
            overview={"method_summary": "Test method"},
            evidence_chunks=[
                {
                    "section_title": "Method",
                    "page_num": 1,
                    "chunk_type": "paragraph",
                    "content": "Test method detail",
                }
            ],
            conversation_context={
                "recent_messages": [{"role": "user", "content_md": "上一轮问题"}],
                "recent_questions": ["上一轮问题"],
                "session_summary": {
                    "summary_text": "更早的历史在讨论方法主线",
                    "discussion_topics": ["method"],
                    "key_points": ["讨论过方法主线"],
                    "open_questions": ["那个模块为什么有效"],
                },
            },
            user_memory={
                "read_paper_ids": ["paper-1"],
                "recent_topics": ["RAG"],
                "weak_concepts": ["Attention"],
                "mastered_concepts": ["Transformer"],
                "preferred_explanation_style": "intuitive_with_examples",
                "cross_paper_links": [],
            },
        )
        global_prompt = build_global_agent_answer_prompt("你好")

        self.assertIn("当前会话最近上下文", prompt)
        self.assertIn("当前会话较早历史摘要", prompt)
        self.assertIn("当前用户背景信息", prompt)
        self.assertIn("intuitive_with_examples", prompt)
        self.assertIn("更早的历史在讨论方法主线", prompt)
        self.assertNotIn("先判断问题类型", prompt)
        self.assertNotIn("属于哪一类", prompt)
        self.assertNotIn("记忆不足", global_prompt)
        self.assertNotIn("只有在某类问题时", prompt)

    def test_global_answer_chain_no_longer_returns_memory_style_response(self) -> None:
        answer = RAGService().answer_global_question(
            question="你好",
            conversation_id="session-global-chat",
            selected_model="disabled-test-model",
        )

        self.assertNotIn("记忆不足", answer["answer_md"])
        self.assertNotIn("阅读记忆", answer["answer_md"])
        self.assertEqual(answer["model_used"], "global-chat")

    def test_paper_answer_chain_still_uses_paper_context_without_memory_injection(self) -> None:
        repo = LocalStoreRepository()
        self._save_test_overview(repo, "paper-context")

        answer = RAGService().answer_question(
            paper_id="paper-context",
            question="这篇论文的方法是什么？",
            conversation_id="session-paper-context",
            selected_model="disabled-test-model",
        )

        self.assertIn("Test method", answer["answer_md"])
        self.assertNotIn("记忆", answer["answer_md"])

    def test_followup_recovers_previous_question_from_short_term_memory(self) -> None:
        repo = LocalStoreRepository()
        self._save_test_overview(repo, "paper-followup")
        memory = ShortTermMemoryService()
        memory.update_short_term_memory(
            conversation_id="session-followup",
            question="这篇论文的方法主线是什么？",
            answer="方法主线是 Test method",
        )

        answer = RAGService().answer_question(
            paper_id="paper-followup",
            question="我刚刚问了什么问题？",
            conversation_id="session-followup",
            selected_model="disabled-test-model",
        )

        self.assertIn("这篇论文的方法主线是什么？", answer["answer_md"])

    def test_followup_falls_back_to_raw_messages_when_structured_memory_missing(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_message(
            {
                "message_id": "m1",
                "session_id": "session-raw-fallback",
                "role": "user",
                "content_md": "前一个真实问题是什么？",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m2",
                "session_id": "session-raw-fallback",
                "role": "assistant",
                "content_md": "刚才在解释方法主线。",
                "citations": [],
                "created_at": "2026-03-14T00:00:01+00:00",
            }
        )

        answer = RAGService().answer_global_question(
            question="上一个问题是什么？",
            conversation_id="session-raw-fallback",
            selected_model="disabled-test-model",
        )

        self.assertIn("前一个真实问题是什么？", answer["answer_md"])

    def test_empty_conversation_reports_no_history_only_when_really_empty(self) -> None:
        answer = RAGService().answer_global_question(
            question="我刚刚问了什么问题？",
            conversation_id="session-empty",
            selected_model="disabled-test-model",
        )

        self.assertIn("还没有更早的问题记录", answer["answer_md"])

    def test_short_term_memory_does_not_cross_global_conversations(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_message(
            {
                "message_id": "m1",
                "session_id": "session-global-a",
                "role": "user",
                "content_md": "global A question",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m2",
                "session_id": "session-global-b",
                "role": "user",
                "content_md": "global B question",
                "citations": [],
                "created_at": "2026-03-14T00:00:01+00:00",
            }
        )

        answer = RAGService().answer_global_question(
            question="上一个问题是什么？",
            conversation_id="session-global-a",
            selected_model="disabled-test-model",
        )

        self.assertIn("global A question", answer["answer_md"])
        self.assertNotIn("global B question", answer["answer_md"])

    def test_short_term_memory_does_not_cross_global_and_paper_chat(self) -> None:
        repo = LocalStoreRepository()
        self._save_test_overview(repo, "paper-isolated")
        repo.create_chat_message(
            {
                "message_id": "m1",
                "session_id": "session-global-isolated",
                "role": "user",
                "content_md": "global only question",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "m2",
                "session_id": "session-paper-isolated",
                "role": "user",
                "content_md": "paper only question",
                "citations": [],
                "created_at": "2026-03-14T00:00:01+00:00",
            }
        )

        answer = RAGService().answer_question(
            paper_id="paper-isolated",
            question="上一个问题是什么？",
            conversation_id="session-paper-isolated",
            selected_model="disabled-test-model",
        )

        self.assertIn("paper only question", answer["answer_md"])
        self.assertNotIn("global only question", answer["answer_md"])

    def test_can_list_global_chat_session_memory_views(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-global-memory",
                "conversation_id": "session-global-memory",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Global Memory",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "message-global-memory-1",
                "session_id": "session-global-memory",
                "role": "user",
                "content_md": "global raw message",
                "citations": [],
                "created_at": "2026-03-14T00:00:00+00:00",
            }
        )
        memory = ShortTermMemoryService()
        memory.update_short_term_memory(
            conversation_id="session-global-memory",
            question="global recent question",
            answer="global answer",
        )
        views = memory.list_session_memory_views()

        self.assertEqual(len(views), 1)
        self.assertEqual(views[0]["conversation_type"], "global_chat")
        self.assertIn("global recent question", views[0]["recent_questions"])
        self.assertEqual(views[0]["recent_messages"][0]["message_id"], "message-global-memory-1")

    def test_can_list_paper_chat_session_memory_views(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-memory-view",
                "title": "Paper Memory View",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 10,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_session(
            {
                "session_id": "session-paper-memory",
                "conversation_id": "session-paper-memory",
                "conversation_type": ConversationType.PAPER_CHAT,
                "paper_id": "paper-memory-view",
                "title": "Paper Memory",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        memory = ShortTermMemoryService()
        memory.update_short_term_memory(
            conversation_id="session-paper-memory",
            question="paper recent question",
            answer="paper answer",
        )
        views = memory.list_session_memory_views()

        self.assertEqual(len(views), 1)
        self.assertEqual(views[0]["conversation_type"], "paper_chat")
        self.assertEqual(views[0]["paper_title"], "Paper Memory View")

    def test_empty_conversation_memory_view_shows_empty_state(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-empty-view",
                "conversation_id": "session-empty-view",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Empty View",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        view = ShortTermMemoryService().get_session_memory_view("session-empty-view")

        self.assertTrue(view["is_empty"])
        self.assertEqual(view["recent_messages"], [])
        self.assertEqual(view["recent_questions"], [])

    def test_clearing_one_conversation_short_term_memory_does_not_affect_others(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-clear-a",
                "conversation_id": "session-clear-a",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Clear A",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.create_chat_session(
            {
                "session_id": "session-clear-b",
                "conversation_id": "session-clear-b",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Clear B",
                "created_at": "2026-03-14T00:00:01+00:00",
                "updated_at": "2026-03-14T00:00:01+00:00",
            }
        )
        memory = ShortTermMemoryService()
        memory.update_short_term_memory("session-clear-a", "question a", "answer a")
        memory.update_short_term_memory("session-clear-b", "question b", "answer b")
        repo.create_chat_message(
            {
                "message_id": "message-clear-a",
                "session_id": "session-clear-a",
                "role": "user",
                "content_md": "raw a",
                "citations": [],
                "created_at": "2026-03-14T00:00:02+00:00",
            }
        )
        repo.create_chat_message(
            {
                "message_id": "message-clear-b",
                "session_id": "session-clear-b",
                "role": "user",
                "content_md": "raw b",
                "citations": [],
                "created_at": "2026-03-14T00:00:03+00:00",
            }
        )

        memory.clear_short_term_memory("session-clear-a")
        view_a = memory.get_session_memory_view("session-clear-a")
        view_b = memory.get_session_memory_view("session-clear-b")

        self.assertTrue(view_a["is_empty"])
        self.assertEqual(view_a["recent_messages"], [])
        self.assertIn("question b", view_b["recent_questions"])
        self.assertEqual(view_b["recent_messages"][0]["content_md"], "raw b")

    def test_instant_memory_keeps_only_latest_five_qa_pairs(self) -> None:
        memory = ShortTermMemoryService()

        for index in range(6):
            memory.update_short_term_memory(
                conversation_id="session-window-five",
                question=f"question {index}",
                answer=f"answer {index}",
            )

        context = memory.build_context("session-window-five")

        self.assertEqual(context["recent_questions"], [f"question {index}" for index in range(1, 6)])
        self.assertEqual(context["session_summary"]["summary_text"], "")

    def test_expired_messages_move_into_pending_summary_buffer(self) -> None:
        repo = LocalStoreRepository()
        memory = ShortTermMemoryService()

        for index in range(5):
            self._append_user_message(repo, "session-summary-pending", index, f"question {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-pending",
                question=f"question {index}",
                answer=f"answer {index}",
            )
            self._append_assistant_message(repo, "session-summary-pending", index, f"answer {index}")

        stored = memory.get_short_term_memory("session-summary-pending")

        self.assertGreaterEqual(len(stored["pending_messages"]), 1)
        self.assertEqual(stored["session_summary"]["summary_text"], "")

    def test_summary_updates_after_pending_buffer_reaches_threshold(self) -> None:
        repo = LocalStoreRepository()
        memory = ShortTermMemoryService()

        for index in range(6):
            self._append_user_message(repo, "session-summary-trigger", index, f"question {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-trigger",
                question=f"question {index}",
                answer=f"answer {index}",
            )
            self._append_assistant_message(repo, "session-summary-trigger", index, f"answer {index}")

        stored = memory.get_short_term_memory("session-summary-trigger")

        self.assertEqual(stored["pending_messages"], [])
        self.assertNotEqual(stored["session_summary"]["summary_text"], "")
        self.assertNotEqual(stored["session_summary"]["covered_message_until"], "")

    def test_session_summary_updates_incrementally_instead_of_full_rewrite(self) -> None:
        repo = LocalStoreRepository()
        memory = ShortTermMemoryService()

        for index in range(6):
            self._append_user_message(repo, "session-summary-incremental", index, f"Transformer topic {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-incremental",
                question=f"Transformer topic {index}",
                answer=f"answer {index}",
            )
            self._append_assistant_message(repo, "session-summary-incremental", index, f"answer {index}")

        first_summary = memory.get_short_term_memory("session-summary-incremental")["session_summary"]

        for index in range(6, 7):
            self._append_user_message(repo, "session-summary-incremental", index, f"Retriever topic {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-incremental",
                question=f"Retriever topic {index}",
                answer=f"answer {index}",
            )
            self._append_assistant_message(repo, "session-summary-incremental", index, f"answer {index}")

        second_summary = memory.get_short_term_memory("session-summary-incremental")["session_summary"]

        self.assertIn("Transformer", "".join(second_summary["discussion_topics"]))
        self.assertEqual(first_summary["covered_message_until"], second_summary["covered_message_until"])

        for index in range(7, 12):
            self._append_user_message(repo, "session-summary-incremental", index, f"Retriever topic {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-incremental",
                question=f"Retriever topic {index}",
                answer=f"answer {index}",
            )
            self._append_assistant_message(repo, "session-summary-incremental", index, f"answer {index}")

        third_summary = memory.get_short_term_memory("session-summary-incremental")["session_summary"]

        self.assertIn("Transformer", "".join(third_summary["discussion_topics"]))
        self.assertIn("Retriever", "".join(third_summary["discussion_topics"]))
        self.assertNotEqual(second_summary["covered_message_until"], third_summary["covered_message_until"])

    def test_low_signal_turns_do_not_pollute_session_summary(self) -> None:
        repo = LocalStoreRepository()
        memory = ShortTermMemoryService()

        for index, question in enumerate(["你好", "继续", "谢谢", "好的", "attention 机制是什么", "它为什么有效"]):
            self._append_user_message(repo, "session-summary-low-signal", index, question)
            memory.update_short_term_memory(
                conversation_id="session-summary-low-signal",
                question=question,
                answer="assistant answer",
            )
            self._append_assistant_message(repo, "session-summary-low-signal", index, "assistant answer")

        stored = memory.get_short_term_memory("session-summary-low-signal")

        self.assertNotIn("你好", stored["session_summary"]["summary_text"])
        self.assertNotIn("谢谢", stored["session_summary"]["summary_text"])

    def test_session_summary_does_not_cross_conversations(self) -> None:
        repo = LocalStoreRepository()
        memory = ShortTermMemoryService()

        for index in range(6):
            self._append_user_message(repo, "session-summary-a", index, f"Alpha topic {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-a",
                question=f"Alpha topic {index}",
                answer="alpha answer",
            )
            self._append_assistant_message(repo, "session-summary-a", index, "alpha answer")
            self._append_user_message(repo, "session-summary-b", index, f"Beta topic {index}")
            memory.update_short_term_memory(
                conversation_id="session-summary-b",
                question=f"Beta topic {index}",
                answer="beta answer",
            )
            self._append_assistant_message(repo, "session-summary-b", index, "beta answer")

        summary_a = memory.get_short_term_memory("session-summary-a")["session_summary"]["summary_text"]
        summary_b = memory.get_short_term_memory("session-summary-b")["session_summary"]["summary_text"]

        self.assertIn("Alpha", summary_a)
        self.assertNotIn("Beta", summary_a)
        self.assertIn("Beta", summary_b)
        self.assertNotIn("Alpha", summary_b)

    def test_can_list_session_summary_views(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-summary-view",
                "conversation_id": "session-summary-view",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Summary View",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        memory = ShortTermMemoryService()
        for index in range(6):
            self._append_user_message(repo, "session-summary-view", index, f"topic {index}")
            memory.update_short_term_memory("session-summary-view", f"topic {index}", f"answer {index}")
            self._append_assistant_message(repo, "session-summary-view", index, f"answer {index}")

        views = memory.list_session_summary_views()

        self.assertEqual(len(views), 1)
        self.assertEqual(views[0]["conversation_id"], "session-summary-view")
        self.assertNotEqual(views[0]["summary_text"], "")
        self.assertGreaterEqual(views[0]["pending_messages_count"], 0)

    def test_empty_session_summary_view_shows_empty_state(self) -> None:
        repo = LocalStoreRepository()
        repo.create_chat_session(
            {
                "session_id": "session-summary-empty",
                "conversation_id": "session-summary-empty",
                "conversation_type": ConversationType.GLOBAL_CHAT,
                "paper_id": None,
                "title": "Summary Empty",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )

        view = ShortTermMemoryService().get_session_summary_view("session-summary-empty")

        self.assertTrue(view["is_empty"])
        self.assertEqual(view["summary_text"], "")
        self.assertEqual(view["discussion_topics"], [])

    def test_ingestion_driven_user_memory_updates_read_history_topics_and_candidates_only(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-user-ingest",
                "title": "Retrieval Routing for RAG",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": ["Retrieval", "Routing"],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        overview = {
            "prerequisite_knowledge": [{"topic": "Dense Retrieval"}],
            "recommended_readings": [
                {
                    "title": "HyDE for Retrieval",
                    "relation_to_current_paper": "baseline",
                }
            ],
        }

        memory = MemoryService().update_user_memory_from_ingestion(
            paper_id="paper-user-ingest",
            overview=overview,
        )

        self.assertIn("paper-user-ingest", memory["read_paper_ids"])
        self.assertIn("Dense Retrieval", memory["recent_topics"])
        self.assertEqual(memory["weak_concepts"], [])
        self.assertEqual(memory["mastered_concepts"], [])
        self.assertEqual(memory["cross_paper_links"], [])
        self.assertEqual(memory["paper_link_candidates"][0]["target_paper_id"], "ext:HyDE for Retrieval")

    def test_conversation_driven_user_memory_updates_understanding_state_only(self) -> None:
        service = MemoryService()
        service.update_user_memory_from_ingestion(
            paper_id="paper-keep-read",
            overview={"prerequisite_knowledge": [{"topic": "Graph Neural Networks"}]},
        )

        memory = service.update_user_memory_from_conversation(
            paper_id="paper-keep-read",
            question="我还是没懂 Transformer attention 是什么，能通俗举例吗？",
            answer="我用一个直观例子解释 attention。",
            overview={
                "recommended_readings": [
                    {
                        "title": "Attention Is All You Need",
                        "relation_to_current_paper": "foundation",
                    }
                ]
            },
        )

        self.assertIn("paper-keep-read", memory["read_paper_ids"])
        self.assertIn("Transformer", memory["weak_concepts"])
        self.assertEqual(memory["preferred_explanation_style"], "intuitive_with_examples")
        self.assertEqual(memory["recent_topics"], ["Graph Neural Networks"])
        self.assertEqual(memory["cross_paper_links"], [])

    def test_user_entity_memory_is_saved_under_local_user_scope(self) -> None:
        service = MemoryService()
        service.update_user_memory_from_conversation(
            question="我没懂 Retrieval 是什么",
            answer="我来解释 Retrieval",
        )

        repo = LocalStoreRepository()
        stored = repo.get_scoped_memory("user:local-user")

        self.assertIsNotNone(stored)
        self.assertEqual(stored["user_id"], "local-user")
        self.assertEqual(stored["scope_type"], "user")

    def test_different_conversations_share_the_same_user_entity_memory(self) -> None:
        service = MemoryService()
        service.update_user_memory_from_conversation(
            question="我没懂 Attention 是什么",
            answer="我来解释 Attention",
        )

        first = service.get_user_memory()
        second = service.get_user_memory()

        self.assertEqual(first["scope_id"], "local-user")
        self.assertEqual(second["scope_id"], "local-user")
        self.assertIn("Attention", second["weak_concepts"])

    def test_conversation_driven_memory_can_confirm_mastery_and_cross_paper_links(self) -> None:
        memory = MemoryService().update_user_memory_from_conversation(
            paper_id="paper-compare",
            question="我明白了 MoE 路由；顺便对比一下这篇和 HyDE 的区别。",
            answer="可以从路由机制和检索构造两个角度比较。",
            overview={
                "recommended_readings": [
                    {
                        "title": "HyDE",
                        "relation_to_current_paper": "comparison",
                    }
                ]
            },
        )

        self.assertIn("MoE", memory["mastered_concepts"])
        self.assertNotIn("MoE", memory["weak_concepts"])
        self.assertEqual(memory["cross_paper_links"][0]["target_paper_id"], "ext:HyDE")

    def test_agent_writes_user_memory_from_conversation_without_touching_prompt_memory_chain(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-agent-memory",
                "title": "Paper Agent Memory",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        self._save_test_overview(repo, "paper-agent-memory")

        PaperCompanionAgent().answer(
            paper_id="paper-agent-memory",
            session_id="session-agent-memory",
            question="我没懂 Retrieval 是什么，能通俗举例吗？",
            selected_model="disabled-test-model",
        )

        memory = MemoryService().get_user_memory()
        self.assertIn("Retrieval", memory["weak_concepts"])
        self.assertEqual(memory["preferred_explanation_style"], "intuitive_with_examples")

    def test_paper_entity_memory_card_can_be_built_from_overview(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-card-a",
                "title": "Paper Card A",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        overview = {
            "research_motivation": "此前方法在复杂查询下不稳定。",
            "problem_definition": "希望让检索路由更稳健。",
            "main_contributions": ["提出新的 routing 模块", "引入更细粒度的证据选择"],
            "method_summary": "通过分层路由先选证据类型，再选具体片段。",
            "transferable_insights": [{"idea": "分层路由可迁移到别的文档系统"}],
            "main_experiments": [
                {
                    "claim": "在多个 benchmark 上效果更好。",
                    "evidence": "使用 NQ 与 HotpotQA 做测试。",
                    "what_it_proves": "新路由设计有效。",
                }
            ],
            "prerequisite_knowledge": [{"topic": "RAG"}],
            "key_modules": [{"name": "Routing Module"}],
        }

        card = PaperEntityMemoryService().upsert_from_overview("paper-card-a", overview)

        self.assertEqual(card["paper_id"], "paper-card-a")
        self.assertEqual(card["paper_title"], "Paper Card A")
        self.assertIn("此前方法在复杂查询下不稳定", card["summary_card"])
        self.assertIn("分层路由", card["method"])
        self.assertIn("NQ 与 HotpotQA", card["test_data"])
        self.assertIn("多个 benchmark 上效果更好", card["key_results"])

    def test_each_paper_has_only_one_paper_entity_memory_card(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-card-single",
                "title": "Paper Card Single",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        service = PaperEntityMemoryService()
        service.upsert_from_overview("paper-card-single", {"method_summary": "第一版"})
        service.upsert_from_overview("paper-card-single", {"method_summary": "第二版"})

        cards = service.list_cards()

        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["paper_id"], "paper-card-single")
        self.assertEqual(cards[0]["method"], "第二版")

    def test_paper_entity_memory_cards_are_isolated_between_papers(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-card-1",
                "title": "Paper Card 1",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:00+00:00",
                "updated_at": "2026-03-14T00:00:00+00:00",
            }
        )
        repo.upsert_paper(
            {
                "id": "paper-card-2",
                "title": "Paper Card 2",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "Agents",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-14T00:00:01+00:00",
                "updated_at": "2026-03-14T00:00:01+00:00",
            }
        )
        service = PaperEntityMemoryService()
        service.upsert_from_overview("paper-card-1", {"method_summary": "方法一"})
        service.upsert_from_overview("paper-card-2", {"method_summary": "方法二"})

        first = service.get_card("paper-card-1")
        second = service.get_card("paper-card-2")

        self.assertEqual(first["method"], "方法一")
        self.assertEqual(second["method"], "方法二")
        self.assertNotEqual(first["paper_id"], second["paper_id"])


if __name__ == "__main__":
    unittest.main()
