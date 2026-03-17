import tempfile
import unittest

from app.core.config import settings
from app.repositories.local_store import LocalStoreRepository
from app.schemas.chat import ConversationType
from app.services.memory.service import MemoryService


class LongTermWritePolicyTestCase(unittest.TestCase):
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
    def _create_conversation(
        repo: LocalStoreRepository,
        *,
        conversation_id: str,
        conversation_type: str,
        paper_id: str | None = None,
        title: str = "Conversation",
    ) -> None:
        repo.create_chat_session(
            {
                "session_id": conversation_id,
                "conversation_id": conversation_id,
                "conversation_type": conversation_type,
                "paper_id": paper_id,
                "title": title,
                "created_at": "2026-03-16T00:00:00+00:00",
                "updated_at": "2026-03-16T00:00:00+00:00",
            }
        )

    @staticmethod
    def _append_user_message(repo: LocalStoreRepository, conversation_id: str, message_id: str, content: str) -> None:
        repo.create_chat_message(
            {
                "message_id": message_id,
                "session_id": conversation_id,
                "role": "user",
                "content_md": content,
                "citations": [],
                "created_at": "2026-03-16T00:00:00+00:00",
            }
        )

    def test_global_chat_confusion_generates_long_term_candidate(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-global-policy",
            conversation_type=ConversationType.GLOBAL_CHAT,
            title="Global Policy",
        )

        decision = MemoryService().build_long_term_write_decision(
            conversation_id="session-global-policy",
            paper_id=None,
            question="我没看懂 Retrieval 这个概念是什么意思？",
            answer="我来先用直观方式解释 Retrieval。",
        )

        self.assertTrue(decision["should_write"])
        self.assertEqual(decision["writes"][0]["source_scope"], ConversationType.GLOBAL_CHAT)
        self.assertEqual(decision["writes"][0]["conversation_id"], "session-global-policy")
        self.assertIsNone(decision["writes"][0]["paper_id"])

    def test_paper_chat_confusion_generates_long_term_candidate(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-paper-policy",
            conversation_type=ConversationType.PAPER_CHAT,
            paper_id="paper-policy",
            title="Paper Policy",
        )

        decision = MemoryService().build_long_term_write_decision(
            conversation_id="session-paper-policy",
            paper_id="paper-policy",
            question="这篇论文的奖励建模我没看懂，为什么这样设计？",
            answer="因为它要避免模型用长度作弊，所以做了解耦设计。",
        )

        self.assertTrue(decision["should_write"])
        self.assertEqual(decision["writes"][0]["source_scope"], ConversationType.PAPER_CHAT)
        self.assertEqual(decision["writes"][0]["paper_id"], "paper-policy")

    def test_low_signal_small_talk_is_ignored(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-low-signal",
            conversation_type=ConversationType.GLOBAL_CHAT,
        )

        decision = MemoryService().build_long_term_write_decision(
            conversation_id="session-low-signal",
            paper_id=None,
            question="继续",
            answer="好的，我继续。",
        )

        self.assertFalse(decision["should_write"])
        self.assertEqual(decision["reason"], "low_signal_turn")
        self.assertEqual(decision["writes"], [])

    def test_method_summary_turn_generates_high_value_candidate(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-method",
            conversation_type=ConversationType.PAPER_CHAT,
            paper_id="paper-method",
        )

        decision = MemoryService().build_long_term_write_decision(
            conversation_id="session-method",
            paper_id="paper-method",
            question="这篇论文的方法主线是什么？",
            answer="方法主线是把奖励拆成长度相关和内容相关两部分，再只用去长度化奖励训练策略。",
        )

        method_actions = [item for item in decision["writes"] if item["memory_type"] == "method_summary"]
        self.assertTrue(method_actions)
        self.assertGreaterEqual(method_actions[0]["confidence"], 0.8)
        self.assertEqual(method_actions[0]["metadata"]["confidence_level"], "medium")

    def test_repeated_concept_increases_confidence(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-repeat",
            conversation_type=ConversationType.GLOBAL_CHAT,
        )

        first = MemoryService().build_long_term_write_decision(
            conversation_id="session-repeat",
            paper_id=None,
            question="我没看懂 Retrieval 是什么",
            answer="我先解释 Retrieval。",
        )
        base_confidence = first["writes"][0]["confidence"]

        self._append_user_message(repo, "session-repeat", "m1", "我还是没懂 Retrieval 为什么有效")

        second = MemoryService().build_long_term_write_decision(
            conversation_id="session-repeat",
            paper_id=None,
            question="我还是没懂 Retrieval 到底是什么意思",
            answer="我们再解释一次 Retrieval 的作用。",
        )
        repeated_confidence = second["writes"][0]["confidence"]

        self.assertGreater(repeated_confidence, base_confidence)

    def test_output_shape_is_unified(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-shape",
            conversation_type=ConversationType.PAPER_CHAT,
            paper_id="paper-shape",
        )

        decision = MemoryService().build_long_term_write_decision(
            conversation_id="session-shape",
            paper_id="paper-shape",
            question="这篇和 HyDE 有什么区别？",
            answer="一个更偏奖励解耦，一个更偏假设文档构造。",
        )

        self.assertTrue(decision["writes"])
        action = decision["writes"][0]
        self.assertIn("memory_type", action)
        self.assertIn("memory_text", action)
        self.assertIn("source_type", action)
        self.assertIn("source_scope", action)
        self.assertIn("conversation_id", action)
        self.assertIn("paper_id", action)
        self.assertIn("confidence", action)
        self.assertIn("metadata", action)

    def test_long_term_write_decision_can_be_recorded_into_unified_store(self) -> None:
        repo = LocalStoreRepository()
        self._create_conversation(
            repo,
            conversation_id="session-record",
            conversation_type=ConversationType.GLOBAL_CHAT,
            title="Record Session",
        )

        service = MemoryService()
        decision = service.build_long_term_write_decision(
            conversation_id="session-record",
            paper_id=None,
            question="我没看懂 Retrieval 为什么有效",
            answer="因为它把候选范围先缩小，再交给生成模块使用。",
        )
        recorded = service.record_long_term_write_decision(decision)
        stored_items = service.list_long_term_memory_items()

        self.assertTrue(recorded)
        self.assertEqual(len(stored_items), 1)
        self.assertEqual(stored_items[0]["conversation_id"], "session-record")
        self.assertEqual(stored_items[0]["conversation_title"], "Record Session")

    def test_delete_paper_removes_related_long_term_memory_items(self) -> None:
        repo = LocalStoreRepository()
        repo.upsert_paper(
            {
                "id": "paper-delete-ltm",
                "title": "Paper Delete LTM",
                "authors": [],
                "abstract": "",
                "status": "ready",
                "progress_percent": 100,
                "category": "RAG",
                "tags": [],
                "file_path": "",
                "created_at": "2026-03-16T00:00:00+00:00",
                "updated_at": "2026-03-16T00:00:00+00:00",
            }
        )
        self._create_conversation(
            repo,
            conversation_id="session-paper-delete",
            conversation_type=ConversationType.PAPER_CHAT,
            paper_id="paper-delete-ltm",
            title="Paper Delete Session",
        )
        service = MemoryService()
        decision = service.build_long_term_write_decision(
            conversation_id="session-paper-delete",
            paper_id="paper-delete-ltm",
            question="这篇论文的方法主线是什么？",
            answer="方法主线是先分解奖励，再只保留内容相关信号。",
        )
        service.record_long_term_write_decision(decision)

        repo.delete_paper("paper-delete-ltm")

        self.assertEqual(service.list_long_term_memory_items(), [])


if __name__ == "__main__":
    unittest.main()
