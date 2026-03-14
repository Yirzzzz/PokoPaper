import json
import logging
import re
from hashlib import sha1
from datetime import UTC, datetime
from typing import Any

from app.repositories.factory import get_repository
from app.schemas.memory import (
    CrossPaperRecallResult,
    MemoryRetrievalResult,
    MemoryWriteAction,
    MemoryWriteDecision,
    RecalledPaperCandidate,
    RetrievedMemoryItem,
)
from app.schemas.memory import (
    CrossPaperLinkItem,
    PaperLinkItem,
    PaperMemoryRecord,
    SessionMemoryRecord,
    UserMemoryRecord,
)

DEFAULT_USER_ID = "local-user"
logger = logging.getLogger(__name__)
LOW_SIGNAL_EXACT = {
    "你好",
    "您好",
    "hi",
    "hello",
    "谢谢",
    "thank you",
    "thanks",
    "继续",
    "再说一遍",
    "展开一点",
    "举个例子",
}
LOW_SIGNAL_PREFIXES = ("继续", "再说", "展开", "举个例子", "详细说")
SESSION_RETRIEVAL_LIMIT = 2
PAPER_RETRIEVAL_LIMIT = 3
USER_RETRIEVAL_LIMIT = 2
GLOBAL_SESSION_MEMORY_PAPER_ID = "global-reading"
SESSION_ITEM_TYPES = {"conversation_summary", "recent_question", "recent_turn_summary", "active_topic"}
PAPER_ITEM_TYPES = {
    "progress_status",
    "last_read_section",
    "stuck_point",
    "key_question",
    "important_takeaway",
    "method_summary",
    "experiment_takeaway",
    "concept_seen",
    "linked_paper",
}
USER_ITEM_TYPES = {
    "read_paper",
    "preferred_explanation_style",
    "topic_interest",
    "weak_concept",
    "mastered_concept",
    "cross_paper_link",
}


class MemoryService:
    def __init__(self) -> None:
        self.repo = get_repository()

    @staticmethod
    def session_scope(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def paper_scope(paper_id: str) -> str:
        return f"paper:{paper_id}"

    @staticmethod
    def user_scope(user_id: str = DEFAULT_USER_ID) -> str:
        return f"user:{user_id}"

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

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _append_unique(items: list[str], value: str, limit: int) -> list[str]:
        normalized = value.strip()
        if not normalized:
            return items[-limit:]
        merged = [item for item in items if item != normalized]
        merged.append(normalized)
        return merged[-limit:]

    @staticmethod
    def _append_unique_dict(items: list[dict], new_item: dict, identity_key: str, limit: int) -> list[dict]:
        identity = new_item.get(identity_key)
        merged = [item for item in items if item.get(identity_key) != identity]
        merged.append(new_item)
        return merged[-limit:]

    @staticmethod
    def _safe_string(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @classmethod
    def _extract_concepts(cls, text: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z\-\+]{2,}", text)
        seen: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if not cls._is_meaningful_topic(normalized):
                continue
            lowered = normalized.lower()
            if lowered in {"what", "why", "how", "this", "that", "with", "from", "into"}:
                continue
            if normalized not in seen:
                seen.append(normalized)
            if len(seen) == 6:
                break
        return seen

    @staticmethod
    def _looks_like_confusion(question: str) -> bool:
        lowered = question.lower()
        markers = ["不理解", "没懂", "看不懂", "不会", "什么意思", "是什么", "不太明白"]
        return any(marker in question for marker in markers) or "what is" in lowered

    @staticmethod
    def _looks_like_mastery(question: str) -> bool:
        markers = ["明白了", "懂了", "理解了", "掌握了"]
        return any(marker in question for marker in markers)

    @staticmethod
    def _infer_topic_hints(question: str, overview: dict | None = None) -> list[str]:
        topics: list[str] = []
        if overview:
            topics.extend([item.get("topic", "") for item in overview.get("prerequisite_knowledge", [])])
        topics.extend(MemoryService._extract_concepts(question))
        deduped: list[str] = []
        for topic in topics:
            cleaned = topic.strip()
            if not MemoryService._is_meaningful_topic(cleaned):
                continue
            if cleaned not in deduped:
                deduped.append(cleaned)
            if len(deduped) == 4:
                break
        return deduped

    @staticmethod
    def _looks_like_method_question(question: str) -> bool:
        lowered = question.lower()
        return any(token in question for token in ["方法", "模块", "设计", "为什么这样设计"]) or any(
            token in lowered for token in ["method", "module", "architecture", "loss"]
        )

    @staticmethod
    def _looks_like_experiment_question(question: str) -> bool:
        lowered = question.lower()
        return any(token in question for token in ["实验", "消融", "对比", "baseline"]) or any(
            token in lowered for token in ["experiment", "ablation", "result", "baseline"]
        )

    @staticmethod
    def _looks_like_comparison(question: str) -> bool:
        lowered = question.lower()
        return any(token in question for token in ["区别", "对比", "相比", "联系"]) or any(
            token in lowered for token in ["compare", "difference", "similar"]
        )

    @staticmethod
    def _looks_like_low_signal(question: str) -> bool:
        normalized = question.strip().lower()
        if not normalized:
            return True
        if normalized in LOW_SIGNAL_EXACT:
            return True
        if any(normalized.startswith(prefix) for prefix in LOW_SIGNAL_PREFIXES):
            return True
        return len(normalized) <= 3

    @staticmethod
    def _looks_like_global_reading_recall(question: str) -> bool:
        markers = [
            "我阅读过的",
            "我读过哪些",
            "我最近主要在看",
            "我最近看过哪些",
            "我以前在哪篇",
            "我之前看过哪篇",
            "我最近主要在看什么主题",
        ]
        lowered = question.lower()
        return any(marker in question for marker in markers) or (
            ("我" in question or "最近" in question or "以前" in question)
            and any(token in lowered for token in ["papers", "paper", "topic", "method", "concept", "loss"])
        )

    @classmethod
    def _query_focus_tokens(cls, question: str) -> set[str]:
        stop_tokens = {
            "我",
            "之前",
            "以前",
            "最近",
            "哪些",
            "哪篇",
            "什么",
            "论文",
            "papers",
            "paper",
            "topic",
            "topics",
            "method",
            "methods",
            "concept",
            "concepts",
        }
        tokens = set(cls._tokenize_text(question))
        tokens.update(token.lower() for token in cls._extract_concepts(question))
        return {token for token in tokens if token and token not in stop_tokens}

    def _default_session_memory(self, session_id: str, paper_id: str) -> SessionMemoryRecord:
        return SessionMemoryRecord(
            scope_id=session_id,
            paper_id=paper_id,
            updated_at=self._now(),
        )

    def _default_paper_memory(self, paper_id: str) -> PaperMemoryRecord:
        return PaperMemoryRecord(
            scope_id=paper_id,
            paper_id=paper_id,
        )

    def _build_user_memory(self, user_id: str = DEFAULT_USER_ID) -> UserMemoryRecord:
        papers = self.repo.list_papers()
        active_topics = self._collect_active_topics(papers)
        return UserMemoryRecord(
            scope_id=user_id,
            user_id=user_id,
            read_paper_ids=[paper["id"] for paper in papers],
            preferred_explanation_style="intuitive_then_formula",
            recent_topics=active_topics,
            paper_link_candidates=[],
            weak_concepts=[],
            mastered_concepts=[],
            cross_paper_links=[],
        )

    @staticmethod
    def _infer_explanation_style(question: str, answer: str | None = None) -> str | None:
        combined = f"{question}\n{answer or ''}".lower()
        if any(token in combined for token in ["类比", "通俗", "直观", "举例", "example", "intuition"]):
            return "intuitive_with_examples"
        if any(token in combined for token in ["一步一步", "逐步", "step by step", "详细推导"]):
            return "step_by_step"
        if any(token in combined for token in ["公式", "推导", "数学", "equation", "derivation", "proof"]):
            return "formula_first"
        return None

    def _infer_paper_link_candidates(self, paper_id: str, overview: dict | None = None) -> list[dict[str, str]]:
        if not overview:
            return []
        candidates: list[dict[str, str]] = []
        for item in overview.get("recommended_readings", [])[:4]:
            title = self._safe_string(item.get("title"))
            if not title:
                continue
            candidates.append(
                CrossPaperLinkItem(
                    source_paper_id=paper_id,
                    target_paper_id=f"ext:{title}",
                    relation=self._safe_string(item.get("relation_to_current_paper")) or "related",
                ).model_dump()
            )
        return candidates

    def get_overview(self) -> dict:
        papers = self.repo.list_papers()
        user_memory = self.get_user_memory()

        return {
            "read_papers": len(user_memory.get("read_paper_ids", [])),
            "weak_concepts": user_memory.get("weak_concepts", []),
            "preferred_explanation_style": user_memory.get("preferred_explanation_style", "intuitive_then_formula"),
            "active_topics": user_memory.get("recent_topics", []),
            "recent_stuck_points": [
                {
                    "paper_title": paper["title"],
                    "concept": (
                        (self.get_paper_memory(paper["id"]).get("stuck_points") or ["overview grounding"])[0]
                    ),
                    "last_seen_at": paper["updated_at"],
                }
                for paper in papers[:3]
            ],
        }

    def get_session_memory(self, session_id: str, paper_id: str) -> dict:
        scope_key = self.session_scope(session_id)
        memory = self.repo.get_scoped_memory(scope_key) if hasattr(self.repo, "get_scoped_memory") else None
        if memory is None:
            return self._default_session_memory(session_id, paper_id).model_dump()
        return SessionMemoryRecord(**{**self._default_session_memory(session_id, paper_id).model_dump(), **memory}).model_dump()

    def get_paper_memory(self, paper_id: str) -> dict:
        scope_key = self.paper_scope(paper_id)
        memory = self.repo.get_scoped_memory(scope_key) if hasattr(self.repo, "get_scoped_memory") else self.repo.get_memory(paper_id)
        if memory is None:
            return self._default_paper_memory(paper_id).model_dump()
        return PaperMemoryRecord(**{**self._default_paper_memory(paper_id).model_dump(), **memory}).model_dump()

    def get_user_memory(self, user_id: str = DEFAULT_USER_ID) -> dict:
        scope_key = self.user_scope(user_id)
        stored = self.repo.get_scoped_memory(scope_key) if hasattr(self.repo, "get_scoped_memory") else None
        base = self._build_user_memory(user_id).model_dump()
        merged = UserMemoryRecord(**{**base, **(stored or {})}).model_dump()
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(scope_key, merged)
        return merged

    @staticmethod
    def _tokenize_text(text: str) -> list[str]:
        lowered = text.lower()
        ascii_tokens = re.findall(r"[a-z][a-z0-9_\-\+]{1,}", lowered)
        cjk_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        tokens: list[str] = []
        for token in [*ascii_tokens, *cjk_tokens]:
            if token not in tokens:
                tokens.append(token)
        return tokens[:24]

    @staticmethod
    def _payload_text(payload: dict[str, Any]) -> str:
        parts: list[str] = []
        for value in payload.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(item) for item in value if isinstance(item, str))
        return " ".join(parts)

    @classmethod
    def _build_memory_item_id(cls, scope: str, memory_type: str, payload: dict[str, Any]) -> str:
        if memory_type in {"stuck_point", "concept_seen", "weak_concept", "mastered_concept"}:
            identity = cls._safe_string(payload.get("concept"))
        elif memory_type in {"important_takeaway", "experiment_takeaway"}:
            identity = cls._safe_string(payload.get("takeaway"))
        elif memory_type == "method_summary":
            identity = cls._safe_string(payload.get("summary"))
        elif memory_type == "linked_paper":
            identity = cls._safe_string(payload.get("paper_id"))
        elif memory_type == "cross_paper_link":
            identity = cls._safe_string(payload.get("target_paper_id"))
        elif memory_type in {"recent_question", "key_question"}:
            identity = cls._safe_string(payload.get("question"))
        elif memory_type in {"recent_turn_summary", "conversation_summary"}:
            identity = cls._safe_string(payload.get("summary") or payload.get("content"))
        elif memory_type in {"active_topic", "topic_interest"}:
            identity = cls._safe_string(payload.get("topic"))
        elif memory_type == "read_paper":
            identity = cls._safe_string(payload.get("paper_id"))
        elif memory_type == "preferred_explanation_style":
            identity = cls._safe_string(payload.get("preferred_explanation_style"))
        elif memory_type == "progress_status":
            identity = cls._safe_string(payload.get("status"))
        elif memory_type == "last_read_section":
            identity = cls._safe_string(payload.get("section"))
        else:
            identity = cls._payload_text(payload) or json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = sha1(f"{scope}|{memory_type}|{identity}".encode("utf-8")).hexdigest()[:16]
        return f"mem-{digest}"

    @staticmethod
    def _memory_item_summary(memory_type: str, payload: dict[str, Any]) -> str:
        if memory_type in {"stuck_point", "concept_seen", "weak_concept", "mastered_concept", "active_topic", "topic_interest"}:
            return payload.get("concept") or payload.get("topic") or "-"
        if memory_type in {"important_takeaway", "experiment_takeaway"}:
            return payload.get("takeaway", "-")
        if memory_type == "method_summary":
            return payload.get("summary", "-")
        if memory_type in {"linked_paper", "read_paper"}:
            return payload.get("paper_title") or payload.get("paper_id") or "-"
        if memory_type == "cross_paper_link":
            return payload.get("relation") or payload.get("target_paper_id") or "-"
        if memory_type == "preferred_explanation_style":
            return payload.get("preferred_explanation_style", "-")
        if memory_type in {"recent_question", "recent_turn_summary", "conversation_summary"}:
            return payload.get("question") or payload.get("summary") or payload.get("content") or "-"
        if memory_type == "progress_status":
            return payload.get("status", "-")
        if memory_type == "last_read_section":
            return payload.get("section", "-")
        if memory_type == "key_question":
            return payload.get("question", "-")
        return MemoryService._payload_text(payload)[:240]

    def _get_item_state(self, memory_id: str) -> dict[str, Any]:
        if hasattr(self.repo, "get_memory_item_state"):
            return self.repo.get_memory_item_state(memory_id) or {}
        return {}

    def _list_item_meta(self) -> dict[str, Any]:
        if hasattr(self.repo, "list_memory_item_meta"):
            return self.repo.list_memory_item_meta()
        return {}

    def _list_item_states(self) -> dict[str, Any]:
        if hasattr(self.repo, "list_memory_item_states"):
            return self.repo.list_memory_item_states()
        return {}

    def _memory_item(
        self,
        scope: str,
        scope_type: str,
        scope_id: str,
        memory_type: str,
        payload: dict[str, Any],
        paper_map: dict[str, dict[str, Any]],
        paper_id: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> dict[str, Any]:
        memory_id = self._build_memory_item_id(scope, memory_type, payload)
        state = self._get_item_state(memory_id)
        meta = self.repo.get_memory_item_meta(memory_id) if hasattr(self.repo, "get_memory_item_meta") else None
        resolved_paper_id = paper_id or (meta.get("paper_id") if meta else None)
        paper_title = paper_map.get(resolved_paper_id or "", {}).get("title") if resolved_paper_id else None
        return {
            "memory_id": memory_id,
            "scope": scope,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "memory_type": memory_type,
            "payload": payload,
            "summary": self._memory_item_summary(memory_type, payload),
            "paper_id": resolved_paper_id,
            "paper_title": paper_title,
            "created_at": (meta or {}).get("created_at") or created_at,
            "updated_at": (meta or {}).get("updated_at") or updated_at,
            "is_enabled": state.get("is_enabled", True),
            "write_reason": (meta or {}).get("write_reason"),
            "write_confidence": (meta or {}).get("write_confidence"),
            "source_question": (meta or {}).get("source_question"),
            "source_answer_preview": (meta or {}).get("source_answer_preview"),
        }

    @classmethod
    def _keyword_overlap_score(cls, question: str, payload: dict[str, Any]) -> float:
        question_tokens = set(cls._tokenize_text(question))
        payload_tokens = set(cls._tokenize_text(cls._payload_text(payload)))
        if not question_tokens or not payload_tokens:
            return 0.0
        overlap = len(question_tokens & payload_tokens)
        return min(overlap * 0.12, 0.48)

    @classmethod
    def _infer_retrieval_route(cls, question: str) -> tuple[bool, str | None, str | None]:
        explicit_confusion = any(token in question for token in ["不理解", "没懂", "看不懂", "不会", "什么意思", "不太明白"])
        if cls._looks_like_low_signal(question):
            return False, "low_signal_turn", None
        if cls._looks_like_comparison(question) or any(token in question for token in ["之前那篇", "哪篇", "见过", "最像", "类似"]):
            return True, None, "cross_paper_recall"
        if any(
            token in question
            for token in ["上次", "刚才", "前面", "那个问题", "刚刚", "上一条", "最近那条", "上一个问题", "最近问题"]
        ):
            return True, None, "session_followup"
        if not explicit_confusion and (cls._looks_like_method_question(question) or cls._looks_like_experiment_question(question)):
            return True, None, "paper_understanding"
        if any(token in question for token in ["动机", "贡献", "解决什么问题", "做了什么"]):
            return True, None, "paper_understanding"
        if cls._looks_like_confusion(question):
            return True, None, "concept_support"
        return False, "memory_not_needed", None

    @classmethod
    def _infer_global_retrieval_route(cls, question: str) -> tuple[bool, str | None, str | None]:
        if cls._looks_like_low_signal(question):
            return False, "low_signal_turn", None
        if any(
            token in question
            for token in ["上次", "刚才", "前面", "那个问题", "刚刚", "上一条", "最近那条", "上一个问题", "最近问题"]
        ):
            return True, None, "session_followup"
        if cls._looks_like_global_reading_recall(question):
            return True, None, "global_reading_recall"
        if cls._looks_like_comparison(question) or any(token in question for token in ["之前那篇", "哪篇", "见过", "最像", "类似"]):
            return True, None, "global_reading_recall"
        return False, "memory_not_needed", None

    def _paper_candidates(self, paper_id: str) -> list[RetrievedMemoryItem]:
        paper_memory = self.get_paper_memory(paper_id)
        items: list[RetrievedMemoryItem] = []
        for concept in paper_memory.get("stuck_points", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="stuck_point",
                    payload={"concept": concept},
                )
            )
        for takeaway in paper_memory.get("important_takeaways", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="important_takeaway",
                    payload={"takeaway": takeaway},
                )
            )
        if paper_memory.get("method_summary"):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="method_summary",
                    payload={"summary": paper_memory["method_summary"]},
                )
            )
        for takeaway in paper_memory.get("experiment_takeaways", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="experiment_takeaway",
                    payload={"takeaway": takeaway},
                )
            )
        for concept in paper_memory.get("concepts_seen", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="concept_seen",
                    payload={"concept": concept},
                )
            )
        for link in paper_memory.get("linked_papers", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.paper_scope(paper_id),
                    memory_type="linked_paper",
                    payload=link,
                )
            )
        return items

    def _session_candidates(self, session_id: str, paper_id: str) -> list[RetrievedMemoryItem]:
        session_memory = self.get_session_memory(session_id, paper_id)
        items: list[RetrievedMemoryItem] = []
        for question in session_memory.get("recent_questions", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.session_scope(session_id),
                    memory_type="recent_question",
                    payload={"question": question},
                )
            )
        for summary in session_memory.get("recent_turn_summaries", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.session_scope(session_id),
                    memory_type="recent_turn_summary",
                    payload={"summary": summary},
                )
            )
        for topic in session_memory.get("active_topics", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.session_scope(session_id),
                    memory_type="active_topic",
                    payload={"topic": topic},
                )
            )
        return items

    def _user_candidates(self, user_id: str = DEFAULT_USER_ID) -> list[RetrievedMemoryItem]:
        user_memory = self.get_user_memory(user_id)
        items: list[RetrievedMemoryItem] = []
        for concept in user_memory.get("weak_concepts", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.user_scope(user_id),
                    memory_type="weak_concept",
                    payload={"concept": concept},
                )
            )
        for concept in user_memory.get("mastered_concepts", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.user_scope(user_id),
                    memory_type="mastered_concept",
                    payload={"concept": concept},
                )
            )
        for topic in user_memory.get("recent_topics", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.user_scope(user_id),
                    memory_type="topic_interest",
                    payload={"topic": topic},
                )
            )
        for link in user_memory.get("cross_paper_links", []):
            items.append(
                RetrievedMemoryItem(
                    source_scope=self.user_scope(user_id),
                    memory_type="cross_paper_link",
                    payload=link,
                )
            )
        return items

    @staticmethod
    def _base_score_for_route(route: str, item: RetrievedMemoryItem) -> float:
        memory_type = item.memory_type
        scope = item.source_scope.split(":", 1)[0]
        score = 0.12
        if route == "paper_understanding":
            if scope == "paper":
                score += 0.35
            if memory_type == "method_summary":
                score += 0.38
            if memory_type in {"important_takeaway", "experiment_takeaway"}:
                score += 0.28
            if memory_type == "recent_turn_summary":
                score += 0.18
        elif route == "concept_support":
            if memory_type in {"stuck_point", "weak_concept"}:
                score += 0.44
            if memory_type in {"method_summary", "concept_seen"}:
                score += 0.26
            if scope == "user":
                score += 0.12
        elif route == "cross_paper_recall":
            if memory_type in {"linked_paper", "cross_paper_link"}:
                score += 0.48
            if scope == "user":
                score += 0.2
            if scope == "paper":
                score += 0.12
        elif route == "session_followup":
            if memory_type == "recent_question":
                score += 0.52
            if memory_type == "recent_turn_summary":
                score += 0.46
            if memory_type == "active_topic":
                score += 0.28
            if scope == "session":
                score += 0.18
        return score

    def get_recent_chat_messages(self, session_id: str, limit: int = 6) -> list[dict[str, Any]]:
        if not hasattr(self.repo, "list_chat_messages"):
            return []
        messages = self.repo.list_chat_messages(session_id)
        if limit <= 0:
            return messages
        return messages[-limit:]

    def build_session_followup_context(
        self,
        session_id: str,
        paper_id: str,
        current_question: str | None = None,
    ) -> dict[str, Any]:
        session_memory = self.get_session_memory(session_id=session_id, paper_id=paper_id)
        recent_messages = self.get_recent_chat_messages(session_id, limit=8)
        normalized_current = (current_question or "").strip()
        user_messages = [item for item in recent_messages if item.get("role") == "user"]
        assistant_messages = [item for item in recent_messages if item.get("role") == "assistant"]

        previous_user_messages = user_messages
        if normalized_current and user_messages and (user_messages[-1].get("content_md") or "").strip() == normalized_current:
            previous_user_messages = user_messages[:-1]

        last_user_question = None
        if previous_user_messages:
            last_user_question = previous_user_messages[-1].get("content_md")
        elif session_memory.get("recent_questions"):
            last_user_question = session_memory.get("recent_questions", [])[-1]

        last_turn_summary = session_memory.get("recent_turn_summaries", [])[-1] if session_memory.get("recent_turn_summaries") else None
        last_assistant_message = assistant_messages[-1].get("content_md") if assistant_messages else None

        raw_history = [
            {
                "role": item.get("role"),
                "content_md": item.get("content_md", ""),
                "created_at": item.get("created_at", ""),
            }
            for item in recent_messages[-6:]
        ]
        return {
            "has_history": bool(last_user_question or last_turn_summary or last_assistant_message or raw_history),
            "last_user_question": last_user_question,
            "last_turn_summary": last_turn_summary,
            "last_assistant_message": last_assistant_message,
            "recent_questions": session_memory.get("recent_questions", [])[-3:],
            "recent_turn_summaries": session_memory.get("recent_turn_summaries", [])[-3:],
            "raw_history": raw_history,
        }

    def _score_item(self, question: str, route: str, item: RetrievedMemoryItem) -> float:
        score = self._base_score_for_route(route, item)
        score += self._keyword_overlap_score(question, item.payload)
        if item.source_scope.startswith("paper:"):
            score += 0.08
        return round(min(score, 1.0), 3)

    def retrieve_memory(
        self,
        paper_id: str,
        session_id: str,
        question: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        should_retrieve, reason, route = self._infer_retrieval_route(question.strip())
        if not should_retrieve:
            result = MemoryRetrievalResult(should_retrieve=False, reason=reason, route=route, items=[])
            logger.info(
                "memory.retrieve skipped: reason=%s session=%s paper=%s",
                reason,
                session_id,
                paper_id,
            )
            return result.model_dump()

        scopes: list[str]
        if route == "cross_paper_recall":
            scopes = ["paper", "user", "session"]
        elif route == "concept_support":
            scopes = ["paper", "user", "session"]
        elif route == "session_followup":
            scopes = ["session"]
        else:
            scopes = ["paper", "session", "user"]

        candidates: list[RetrievedMemoryItem] = []
        if "paper" in scopes:
            candidates.extend(self._paper_candidates(paper_id))
        if "session" in scopes:
            candidates.extend(self._session_candidates(session_id, paper_id))
        if "user" in scopes:
            candidates.extend(self._user_candidates(user_id))

        scored: list[RetrievedMemoryItem] = []
        for item in candidates:
            if not self._get_item_state(self._build_memory_item_id(item.source_scope, item.memory_type, item.payload)).get("is_enabled", True):
                continue
            score = self._score_item(question, route or "paper_understanding", item)
            if score < 0.18:
                continue
            scored.append(item.model_copy(update={"score": score}))

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        selected: list[RetrievedMemoryItem] = []
        scope_counts = {"session": 0, "paper": 0, "user": 0}
        scope_limits = {"session": SESSION_RETRIEVAL_LIMIT, "paper": PAPER_RETRIEVAL_LIMIT, "user": USER_RETRIEVAL_LIMIT}
        for item in ranked:
            scope = item.source_scope.split(":", 1)[0]
            if scope_counts[scope] >= scope_limits[scope]:
                continue
            selected.append(item)
            scope_counts[scope] += 1

        result = MemoryRetrievalResult(
            should_retrieve=True,
            reason="retrieved" if selected else "no_matching_memory",
            route=route,
            items=selected,
        )
        logger.info(
            "memory.retrieve result: route=%s session=%s paper=%s scopes=%s selected=%s",
            route,
            session_id,
            paper_id,
            scopes,
            [f"{item.source_scope}:{item.memory_type}:{item.score:.2f}" for item in selected],
        )
        return result.model_dump()

    def retrieve_global_memory(
        self,
        session_id: str,
        question: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        should_retrieve, reason, route = self._infer_global_retrieval_route(question.strip())
        if not should_retrieve:
            result = MemoryRetrievalResult(should_retrieve=False, reason=reason, route=route, items=[])
            logger.info(
                "memory.retrieve.global skipped: reason=%s session=%s",
                reason,
                session_id,
            )
            return result.model_dump()

        session_items = self._session_candidates(session_id, GLOBAL_SESSION_MEMORY_PAPER_ID)
        user_items = self._user_candidates(user_id)
        scored: list[RetrievedMemoryItem] = []
        for item in [*session_items, *user_items]:
            if not self._get_item_state(self._build_memory_item_id(item.source_scope, item.memory_type, item.payload)).get("is_enabled", True):
                continue
            if route == "session_followup":
                score = self._score_item(question, route, item)
            else:
                score = 0.0
                if item.source_scope.startswith("user:"):
                    score += 0.28
                if item.memory_type in {"topic_interest", "weak_concept", "cross_paper_link", "read_paper"}:
                    score += 0.26
                score += self._keyword_overlap_score(question, item.payload)
            if score < 0.18:
                continue
            scored.append(item.model_copy(update={"score": round(min(score, 1.0), 3)}))

        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        selected: list[RetrievedMemoryItem] = []
        scope_counts = {"session": 0, "user": 0}
        scope_limits = {"session": SESSION_RETRIEVAL_LIMIT, "user": USER_RETRIEVAL_LIMIT + 1}
        for item in ranked:
            scope = item.source_scope.split(":", 1)[0]
            if scope not in scope_counts:
                continue
            if scope_counts[scope] >= scope_limits[scope]:
                continue
            selected.append(item)
            scope_counts[scope] += 1

        result = MemoryRetrievalResult(
            should_retrieve=True,
            reason="retrieved" if selected else "no_matching_memory",
            route=route,
            items=selected,
        )
        logger.info(
            "memory.retrieve.global result: session=%s route=%s selected=%s",
            session_id,
            route,
            [f"{item.source_scope}:{item.memory_type}:{item.score:.2f}" for item in selected],
        )
        return result.model_dump()

    def recall_global_reading(
        self,
        question: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        should_recall, reason, route = self._infer_global_retrieval_route(question.strip())
        if not should_recall or route != "global_reading_recall":
            result = CrossPaperRecallResult(should_recall=False, reason=reason or "route_not_global", candidates=[])
            logger.info("memory.recall.global skipped: reason=%s", result.reason)
            return result.model_dump()

        papers = self.repo.list_papers()
        paper_map = {paper["id"]: paper for paper in papers}
        user_memory = self.get_user_memory(user_id)
        question_tokens = set(self._tokenize_text(question))
        focus_tokens = self._query_focus_tokens(question)
        candidates: list[dict[str, Any]] = []

        for read_paper_id in user_memory.get("read_paper_ids", []):
            if read_paper_id.startswith("ext:"):
                continue
            paper = paper_map.get(read_paper_id)
            if not paper:
                continue
            paper_memory = self.get_paper_memory(read_paper_id)
            paper_text = " ".join(
                [
                    paper.get("title", ""),
                    self._safe_string(paper.get("category")),
                    " ".join(paper.get("tags") or []),
                    paper_memory.get("method_summary", ""),
                    " ".join(paper_memory.get("important_takeaways", [])[:3]),
                    " ".join(paper_memory.get("concepts_seen", [])[:6]),
                ]
            )
            score = 0.12
            score += self._keyword_overlap_score(question, {"text": paper_text})
            if any(topic.lower() in paper_text.lower() for topic in user_memory.get("recent_topics", [])):
                score += 0.12
            if any(concept.lower() in paper_text.lower() for concept in user_memory.get("weak_concepts", [])):
                score += 0.1
            if any(token.lower() in paper_text.lower() for token in question_tokens):
                score += 0.08
            metadata_tokens = {
                token.lower()
                for token in [
                    self._safe_string(paper.get("category")),
                    *(paper.get("tags") or []),
                    *paper_memory.get("concepts_seen", []),
                    *self._extract_concepts(paper.get("title", "")),
                ]
                if self._is_meaningful_topic(token)
            }
            if focus_tokens and focus_tokens & metadata_tokens:
                score += min(0.18 + (0.08 * len(focus_tokens & metadata_tokens)), 0.34)
            if score < 0.3:
                continue
            relation_reason = self._candidate_reason("read_paper", question, paper_memory=paper_memory)
            payload = {"paper_id": read_paper_id, "paper_title": paper.get("title")}
            candidates.append(
                RecalledPaperCandidate(
                    paper_id=read_paper_id,
                    title=paper.get("title"),
                    relation_reason=relation_reason,
                    supporting_memory_ids=[self._build_memory_item_id(self.user_scope(user_id), "read_paper", payload)],
                    score=round(min(score, 1.0), 3),
                ).model_dump()
            )

        ranked = [RecalledPaperCandidate(**item) for item in sorted(candidates, key=lambda item: item["score"], reverse=True)[:4]]
        result = CrossPaperRecallResult(
            should_recall=bool(ranked),
            reason="recalled" if ranked else "no_matching_papers",
            candidates=ranked,
        )
        logger.info(
            "memory.recall.global result: candidates=%s",
            [f"{item.paper_id}:{item.score:.2f}:{item.relation_reason}" for item in ranked],
        )
        return result.model_dump()

    def build_global_prompt_memory(
        self,
        session_id: str,
        question: str,
        user_id: str = DEFAULT_USER_ID,
        retrieval_result: dict | None = None,
        recall_result: dict | None = None,
    ) -> dict:
        session_memory = self.get_session_memory(session_id=session_id, paper_id=GLOBAL_SESSION_MEMORY_PAPER_ID)
        user_memory = self.get_user_memory(user_id=user_id)
        retrieval_result = retrieval_result or self.retrieve_global_memory(session_id=session_id, question=question, user_id=user_id)
        recall_result = recall_result or self.recall_global_reading(question=question, user_id=user_id)
        session_items = [RetrievedMemoryItem(**item).model_dump() for item in retrieval_result.get("items", []) if item["source_scope"].startswith("session:")][:SESSION_RETRIEVAL_LIMIT]
        user_items = [RetrievedMemoryItem(**item).model_dump() for item in retrieval_result.get("items", []) if item["source_scope"].startswith("user:")][:USER_RETRIEVAL_LIMIT + 1]
        recall_candidates = [RecalledPaperCandidate(**item).model_dump() for item in recall_result.get("candidates", [])[:3]]
        if retrieval_result.get("route") == "session_followup" and len(session_items) == 0:
            use_summary_fallback = True
            fallback_reason = "missing_session_followup_memory"
        else:
            use_summary_fallback = len(session_items) + len(user_items) == 0
            fallback_reason = "no_retrieved_memory" if use_summary_fallback else None
        raw_followup = self.build_session_followup_context(
            session_id=session_id,
            paper_id=GLOBAL_SESSION_MEMORY_PAPER_ID,
            current_question=question,
        )
        logger.info(
            "memory.inject.global: route=%s session_items=%s user_items=%s recall_candidates=%s fallback_summary=%s",
            retrieval_result.get("route"),
            len(session_items),
            len(user_items),
            len(recall_candidates),
            use_summary_fallback,
        )
        return {
            "scope": {
                "session": self.session_scope(session_id),
                "user": self.user_scope(user_id),
            },
            "preferred_explanation_style": user_memory.get("preferred_explanation_style", "intuitive_then_formula"),
            "memory_retrieval": {
                "should_retrieve": retrieval_result.get("should_retrieve", False),
                "reason": retrieval_result.get("reason"),
                "route": retrieval_result.get("route"),
                "injected_count": len(session_items) + len(user_items),
                "fallback_to_summary": use_summary_fallback,
                "fallback_reason": fallback_reason,
            },
            "session_memory": {
                "items": session_items,
                "active_topics": session_memory.get("active_topics", [])[:3],
            },
            "user_memory": {
                "items": user_items,
                "preferred_explanation_style": user_memory.get("preferred_explanation_style", "intuitive_then_formula"),
                "read_paper_ids": user_memory.get("read_paper_ids", []),
                "recent_topics": user_memory.get("recent_topics", [])[:6],
                "weak_concepts": user_memory.get("weak_concepts", [])[:6],
            },
            "cross_paper_recall": {
                "should_recall": recall_result.get("should_recall", False),
                "reason": recall_result.get("reason"),
                "candidate_count": len(recall_candidates),
                "candidates": recall_candidates,
            },
            "fallback_summary": {
                "conversation_summary": session_memory.get("conversation_summary", "")[:1200] if use_summary_fallback else "",
                "recent_questions": session_memory.get("recent_questions", [])[-2:] if use_summary_fallback else [],
            },
            "raw_message_fallback": raw_followup,
            "recalled_paper_candidates": recall_candidates,
        }

    def _candidate_reason(
        self,
        memory_type: str,
        question: str,
        paper_memory: dict | None = None,
        relation: str | None = None,
    ) -> str:
        if memory_type in {"linked_paper", "cross_paper_link"}:
            return relation or "曾被比较过"
        if "loss" in question.lower() or "loss" in self._payload_text((paper_memory or {})):
            return "loss 相似"
        if any(token in question for token in ["模块", "method", "方法"]):
            return "方法相似"
        if any(token in question for token in ["概念", "见过", "什么意思"]):
            return "概念相似"
        return "同主题相关"

    def recall_cross_paper(
        self,
        paper_id: str,
        session_id: str,
        question: str,
        retrieval_result: dict | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        retrieval_result = retrieval_result or self.retrieve_memory(
            paper_id=paper_id,
            session_id=session_id,
            question=question,
            user_id=user_id,
        )
        if retrieval_result.get("route") != "cross_paper_recall":
            result = CrossPaperRecallResult(should_recall=False, reason="route_not_cross_paper", candidates=[])
            logger.info(
                "memory.recall skipped: reason=%s session=%s paper=%s",
                result.reason,
                session_id,
                paper_id,
            )
            return result.model_dump()

        papers = self.repo.list_papers()
        paper_map = {paper["id"]: paper for paper in papers}
        user_memory = self.get_user_memory(user_id)
        current_paper_memory = self.get_paper_memory(paper_id)
        candidates: dict[str, dict[str, Any]] = {}
        question_lower = question.lower()
        question_tokens = set(self._tokenize_text(question))

        def upsert_candidate(
            candidate_paper_id: str,
            title: str | None,
            relation_reason: str,
            supporting_memory_id: str,
            base_score: float,
            extra_text: str = "",
        ) -> None:
            if candidate_paper_id == paper_id:
                return
            overlap_bonus = 0.0
            combined_text = f"{title or ''} {relation_reason} {extra_text}".strip()
            if question_tokens and combined_text:
                overlap_bonus = self._keyword_overlap_score(question, {"text": combined_text})
            total_score = round(min(base_score + overlap_bonus, 1.0), 3)
            current = candidates.get(candidate_paper_id)
            if current is None or total_score > current["score"]:
                candidates[candidate_paper_id] = {
                    "paper_id": candidate_paper_id,
                    "title": title,
                    "relation_reason": relation_reason,
                    "supporting_memory_ids": [supporting_memory_id],
                    "score": total_score,
                }
            elif supporting_memory_id not in current["supporting_memory_ids"]:
                current["supporting_memory_ids"].append(supporting_memory_id)

        for link in current_paper_memory.get("linked_papers", []):
            memory_id = self._build_memory_item_id(self.paper_scope(paper_id), "linked_paper", link)
            upsert_candidate(
                candidate_paper_id=link.get("paper_id", ""),
                title=link.get("paper_title"),
                relation_reason=self._candidate_reason("linked_paper", question, relation=link.get("relation")),
                supporting_memory_id=memory_id,
                base_score=0.76,
                extra_text=link.get("relation", ""),
            )

        for link in user_memory.get("cross_paper_links", []):
            if link.get("source_paper_id") != paper_id:
                continue
            target_paper_id = link.get("target_paper_id", "")
            title = paper_map.get(target_paper_id, {}).get("title")
            memory_id = self._build_memory_item_id(self.user_scope(user_id), "cross_paper_link", link)
            upsert_candidate(
                candidate_paper_id=target_paper_id,
                title=title,
                relation_reason=self._candidate_reason("cross_paper_link", question, relation=link.get("relation")),
                supporting_memory_id=memory_id,
                base_score=0.72,
                extra_text=link.get("relation", ""),
            )

        recent_topics = set(topic.lower() for topic in user_memory.get("recent_topics", []))
        weak_and_mastered = set(
            item.lower()
            for item in [*user_memory.get("weak_concepts", []), *user_memory.get("mastered_concepts", [])]
        )
        for read_paper_id in user_memory.get("read_paper_ids", []):
            if read_paper_id == paper_id or read_paper_id.startswith("ext:"):
                continue
            candidate_memory = self.get_paper_memory(read_paper_id)
            candidate_text = " ".join(
                [
                    candidate_memory.get("method_summary", ""),
                    " ".join(candidate_memory.get("important_takeaways", [])[:3]),
                    " ".join(candidate_memory.get("concepts_seen", [])[:6]),
                ]
            )
            overlap = self._keyword_overlap_score(question, {"text": candidate_text})
            concept_overlap = len(question_tokens & set(token.lower() for token in candidate_memory.get("concepts_seen", []))) * 0.08
            topic_overlap = 0.12 if any(topic in candidate_text.lower() for topic in recent_topics) else 0.0
            weakness_overlap = 0.14 if any(concept in candidate_text.lower() for concept in weak_and_mastered) else 0.0
            score = round(min(0.22 + overlap + concept_overlap + topic_overlap + weakness_overlap, 1.0), 3)
            if score < 0.36:
                continue
            payload = {"paper_id": read_paper_id, "paper_title": paper_map.get(read_paper_id, {}).get("title")}
            memory_id = self._build_memory_item_id(self.user_scope(user_id), "read_paper", payload)
            upsert_candidate(
                candidate_paper_id=read_paper_id,
                title=paper_map.get(read_paper_id, {}).get("title"),
                relation_reason=self._candidate_reason("read_paper", question, paper_memory=candidate_memory),
                supporting_memory_id=memory_id,
                base_score=score,
                extra_text=candidate_text,
            )

        selected = [
            RecalledPaperCandidate(**candidate)
            for candidate in sorted(candidates.values(), key=lambda item: item["score"], reverse=True)[:3]
        ]
        result = CrossPaperRecallResult(
            should_recall=bool(selected),
            reason="recalled" if selected else "no_matching_papers",
            candidates=selected,
        )
        logger.info(
            "memory.recall result: session=%s paper=%s candidates=%s",
            session_id,
            paper_id,
            [f"{item.paper_id}:{item.score:.2f}:{item.relation_reason}" for item in selected],
        )
        return result.model_dump()

    def build_prompt_memory(
        self,
        paper_id: str,
        session_id: str,
        question: str | None = None,
        user_id: str = DEFAULT_USER_ID,
        retrieval_result: dict | None = None,
        recall_result: dict | None = None,
    ) -> dict:
        session_memory = self.get_session_memory(session_id=session_id, paper_id=paper_id)
        paper_memory = self.get_paper_memory(paper_id=paper_id)
        user_memory = self.get_user_memory(user_id=user_id)
        retrieval_result = retrieval_result or MemoryRetrievalResult(
            should_retrieve=False,
            reason="not_requested",
            route=None,
            items=[],
        ).model_dump()
        recall_result = recall_result or CrossPaperRecallResult(
            should_recall=False,
            reason="not_requested",
            candidates=[],
        ).model_dump()
        items = [RetrievedMemoryItem(**item).model_dump() for item in retrieval_result.get("items", [])]
        recall_candidates = [RecalledPaperCandidate(**item).model_dump() for item in recall_result.get("candidates", [])]
        session_items = [item for item in items if item["source_scope"].startswith("session:")][:SESSION_RETRIEVAL_LIMIT]
        paper_items = [item for item in items if item["source_scope"].startswith("paper:")][:PAPER_RETRIEVAL_LIMIT]
        user_items = [item for item in items if item["source_scope"].startswith("user:")][:USER_RETRIEVAL_LIMIT]
        fallback_reason = None
        if retrieval_result.get("route") == "session_followup" and len(session_items) == 0:
            use_summary_fallback = True
            fallback_reason = "missing_session_followup_memory"
        elif len(items) == 0:
            use_summary_fallback = True
            fallback_reason = "no_retrieved_memory"
        else:
            use_summary_fallback = False
        fallback_summary = {
            "conversation_summary": session_memory.get("conversation_summary", "")[:1200] if use_summary_fallback else "",
            "recent_questions": session_memory.get("recent_questions", [])[-2:] if use_summary_fallback else [],
        }
        raw_followup = self.build_session_followup_context(
            session_id=session_id,
            paper_id=paper_id,
            current_question=question,
        )
        logger.info(
            "memory.inject: route=%s session_items=%s paper_items=%s user_items=%s recall_candidates=%s fallback_summary=%s fallback_reason=%s",
            retrieval_result.get("route"),
            len(session_items),
            len(paper_items),
            len(user_items),
            len(recall_candidates),
            use_summary_fallback,
            fallback_reason,
        )
        return {
            "scope": {
                "session": self.session_scope(session_id),
                "paper": self.paper_scope(paper_id),
                "user": self.user_scope(user_id),
            },
            "preferred_explanation_style": user_memory.get("preferred_explanation_style", "intuitive_then_formula"),
            "memory_retrieval": {
                "should_retrieve": retrieval_result.get("should_retrieve", False),
                "reason": retrieval_result.get("reason"),
                "route": retrieval_result.get("route"),
                "injected_count": len(items),
                "fallback_to_summary": use_summary_fallback,
                "fallback_reason": fallback_reason,
            },
            "retrieved_memory_items": items,
            "session_memory": {
                "items": session_items,
                "active_topics": session_memory.get("active_topics", [])[:3],
            },
            "paper_memory": {
                "items": paper_items,
                "progress_status": paper_memory.get("progress_status", "new"),
                "progress_percent": paper_memory.get("progress_percent", 0),
                "last_read_section": paper_memory.get("last_read_section", "Introduction"),
            },
            "user_memory": {
                "items": user_items,
                "preferred_explanation_style": user_memory.get("preferred_explanation_style", "intuitive_then_formula"),
            },
            "cross_paper_recall": {
                "should_recall": recall_result.get("should_recall", False),
                "reason": recall_result.get("reason"),
                "candidate_count": len(recall_candidates),
                "candidates": recall_candidates[:3],
            },
            "recalled_paper_candidates": recall_candidates,
            "raw_message_fallback": raw_followup,
            "fallback_summary": fallback_summary,
            "conversation_summary": fallback_summary["conversation_summary"],
            "recent_questions": fallback_summary["recent_questions"],
            "active_topics": session_memory.get("active_topics", [])[:3],
            "progress_status": paper_memory.get("progress_status", "new"),
            "progress_percent": paper_memory.get("progress_percent", 0),
            "last_read_section": paper_memory.get("last_read_section", "Introduction"),
        }

    def list_memory_items(
        self,
        scope: str | None = None,
        paper_id: str | None = None,
        memory_type: str | None = None,
        enabled: bool | None = None,
    ) -> list[dict]:
        papers = self.repo.list_papers()
        paper_map = {paper["id"]: paper for paper in papers}
        scoped_memories = self.repo.list_scoped_memories() if hasattr(self.repo, "list_scoped_memories") else {}
        items: list[dict] = []
        for scope_key, memory in scoped_memories.items():
            scope_type, _, scope_id = scope_key.partition(":")
            if scope and scope != scope_type:
                continue
            if scope_type == "session":
                session_paper_id = memory.get("paper_id")
                if paper_id and session_paper_id != paper_id:
                    continue
                updated_at = memory.get("updated_at")
                if memory.get("conversation_summary"):
                    items.append(
                        self._memory_item(
                            scope=scope_key,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            memory_type="conversation_summary",
                            payload={"content": memory["conversation_summary"]},
                            paper_map=paper_map,
                            paper_id=session_paper_id,
                            updated_at=updated_at,
                        )
                    )
                for question_value in memory.get("recent_questions", []):
                    items.append(
                        self._memory_item(
                            scope=scope_key,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            memory_type="recent_question",
                            payload={"question": question_value},
                            paper_map=paper_map,
                            paper_id=session_paper_id,
                            updated_at=updated_at,
                        )
                    )
                for summary in memory.get("recent_turn_summaries", []):
                    items.append(
                        self._memory_item(
                            scope=scope_key,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            memory_type="recent_turn_summary",
                            payload={"summary": summary},
                            paper_map=paper_map,
                            paper_id=session_paper_id,
                            updated_at=updated_at,
                        )
                    )
                for topic in memory.get("active_topics", []):
                    items.append(
                        self._memory_item(
                            scope=scope_key,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            memory_type="active_topic",
                            payload={"topic": topic},
                            paper_map=paper_map,
                            paper_id=session_paper_id,
                            updated_at=updated_at,
                        )
                    )
            elif scope_type == "paper":
                if paper_id and scope_id != paper_id:
                    continue
                updated_at = memory.get("updated_at")
                for stuck in memory.get("stuck_points", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "stuck_point", {"concept": stuck}, paper_map, scope_id, updated_at=updated_at))
                for question_value in memory.get("key_questions", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "key_question", {"question": question_value}, paper_map, scope_id, updated_at=updated_at))
                for takeaway in memory.get("important_takeaways", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "important_takeaway", {"takeaway": takeaway}, paper_map, scope_id, updated_at=updated_at))
                if memory.get("method_summary"):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "method_summary", {"summary": memory["method_summary"]}, paper_map, scope_id, updated_at=updated_at))
                for takeaway in memory.get("experiment_takeaways", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "experiment_takeaway", {"takeaway": takeaway}, paper_map, scope_id, updated_at=updated_at))
                for concept in memory.get("concepts_seen", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "concept_seen", {"concept": concept}, paper_map, scope_id, updated_at=updated_at))
                for link in memory.get("linked_papers", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "linked_paper", link, paper_map, scope_id, updated_at=updated_at))
                if memory.get("progress_status"):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "progress_status", {"status": memory["progress_status"]}, paper_map, scope_id, updated_at=updated_at))
                if memory.get("last_read_section"):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "last_read_section", {"section": memory["last_read_section"]}, paper_map, scope_id, updated_at=updated_at))
            elif scope_type == "user":
                updated_at = memory.get("updated_at")
                for read_paper_id in memory.get("read_paper_ids", []):
                    payload = {"paper_id": read_paper_id, "paper_title": paper_map.get(read_paper_id, {}).get("title")}
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "read_paper", payload, paper_map, read_paper_id, updated_at=updated_at))
                if memory.get("preferred_explanation_style"):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "preferred_explanation_style", {"preferred_explanation_style": memory["preferred_explanation_style"]}, paper_map, updated_at=updated_at))
                for topic in memory.get("recent_topics", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "topic_interest", {"topic": topic}, paper_map, updated_at=updated_at))
                for concept in memory.get("weak_concepts", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "weak_concept", {"concept": concept}, paper_map, updated_at=updated_at))
                for concept in memory.get("mastered_concepts", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "mastered_concept", {"concept": concept}, paper_map, updated_at=updated_at))
                for link in memory.get("cross_paper_links", []):
                    items.append(self._memory_item(scope_key, scope_type, scope_id, "cross_paper_link", link, paper_map, link.get("source_paper_id"), updated_at=updated_at))

        filtered = []
        for item in items:
            if memory_type and item["memory_type"] != memory_type:
                continue
            if paper_id and item.get("paper_id") != paper_id:
                continue
            if enabled is not None and item["is_enabled"] != enabled:
                continue
            filtered.append(item)
        filtered.sort(key=lambda item: (item.get("updated_at") or "", item["memory_id"]), reverse=True)
        return filtered

    def get_memory_item(self, memory_id: str) -> dict:
        item = next((item for item in self.list_memory_items() if item["memory_id"] == memory_id), None)
        if item is None:
            raise KeyError(f"memory item not found: {memory_id}")
        return item

    def set_memory_item_enabled(self, memory_id: str, is_enabled: bool) -> dict:
        item = self.get_memory_item(memory_id)
        state = {
            "is_enabled": is_enabled,
            "updated_at": self._now(),
        }
        if hasattr(self.repo, "save_memory_item_state"):
            self.repo.save_memory_item_state(memory_id, state)
        return {**item, "is_enabled": is_enabled, "updated_at": state["updated_at"]}

    def _remove_item_from_scope(self, item: dict) -> None:
        scope = item["scope"]
        memory = self.repo.get_scoped_memory(scope)
        if memory is None:
            raise KeyError(f"scope not found: {scope}")
        memory_type = item["memory_type"]
        payload = item["payload"]

        if memory_type == "conversation_summary":
            memory["conversation_summary"] = ""
        elif memory_type == "recent_question":
            memory["recent_questions"] = [value for value in memory.get("recent_questions", []) if value != payload.get("question")]
        elif memory_type == "recent_turn_summary":
            memory["recent_turn_summaries"] = [value for value in memory.get("recent_turn_summaries", []) if value != payload.get("summary")]
        elif memory_type == "active_topic":
            memory["active_topics"] = [value for value in memory.get("active_topics", []) if value != payload.get("topic")]
        elif memory_type == "stuck_point":
            memory["stuck_points"] = [value for value in memory.get("stuck_points", []) if value != payload.get("concept")]
        elif memory_type == "key_question":
            memory["key_questions"] = [value for value in memory.get("key_questions", []) if value != payload.get("question")]
        elif memory_type == "important_takeaway":
            memory["important_takeaways"] = [value for value in memory.get("important_takeaways", []) if value != payload.get("takeaway")]
        elif memory_type == "method_summary":
            memory["method_summary"] = ""
        elif memory_type == "experiment_takeaway":
            memory["experiment_takeaways"] = [value for value in memory.get("experiment_takeaways", []) if value != payload.get("takeaway")]
        elif memory_type == "concept_seen":
            memory["concepts_seen"] = [value for value in memory.get("concepts_seen", []) if value != payload.get("concept")]
        elif memory_type == "linked_paper":
            memory["linked_papers"] = [value for value in memory.get("linked_papers", []) if value.get("paper_id") != payload.get("paper_id")]
        elif memory_type == "progress_status":
            memory["progress_status"] = ""
        elif memory_type == "last_read_section":
            memory["last_read_section"] = ""
        elif memory_type == "read_paper":
            memory["read_paper_ids"] = [value for value in memory.get("read_paper_ids", []) if value != payload.get("paper_id")]
        elif memory_type == "preferred_explanation_style":
            memory["preferred_explanation_style"] = ""
        elif memory_type == "topic_interest":
            memory["recent_topics"] = [value for value in memory.get("recent_topics", []) if value != payload.get("topic")]
        elif memory_type == "weak_concept":
            memory["weak_concepts"] = [value for value in memory.get("weak_concepts", []) if value != payload.get("concept")]
        elif memory_type == "mastered_concept":
            memory["mastered_concepts"] = [value for value in memory.get("mastered_concepts", []) if value != payload.get("concept")]
        elif memory_type == "cross_paper_link":
            memory["cross_paper_links"] = [
                value for value in memory.get("cross_paper_links", []) if value.get("target_paper_id") != payload.get("target_paper_id")
            ]
        else:
            raise KeyError(f"unsupported memory type: {memory_type}")

        memory["updated_at"] = self._now()
        self.repo.save_scoped_memory(scope, memory)

    def delete_memory_item(self, memory_id: str) -> None:
        item = self.get_memory_item(memory_id)
        self._remove_item_from_scope(item)
        if hasattr(self.repo, "delete_memory_item_aux"):
            self.repo.delete_memory_item_aux(memory_id)

    def reset_memory(
        self,
        scope: str | None = None,
        paper_id: str | None = None,
        memory_type: str | None = None,
    ) -> dict:
        items = self.list_memory_items(scope=scope, paper_id=paper_id, memory_type=memory_type)
        for item in items:
            self.delete_memory_item(item["memory_id"])
        return {"deleted": len(items)}

    def should_update_summary_memory(self, question: str) -> tuple[bool, str | None]:
        global_should_retrieve, global_reason, global_route = self._infer_global_retrieval_route(question.strip())
        if global_should_retrieve and global_route == "global_reading_recall":
            return True, global_route
        should_retrieve, reason, route = self._infer_retrieval_route(question.strip())
        if not should_retrieve and reason in {"low_signal_turn", "memory_not_needed"}:
            return False, reason
        if route in {"paper_understanding", "concept_support", "cross_paper_recall", "session_followup"}:
            return True, route
        return False, reason or "summary_not_needed"

    def update_session_memory(
        self,
        session_id: str,
        paper_id: str,
        question: str,
        answer: str,
        overview: dict | None = None,
    ) -> dict:
        memory = self.get_session_memory(session_id=session_id, paper_id=paper_id)
        should_update_summary, summary_reason = self.should_update_summary_memory(question)
        if not should_update_summary:
            logger.info(
                "memory.summary skipped: session=%s paper=%s reason=%s",
                session_id,
                paper_id,
                summary_reason,
            )
            record = SessionMemoryRecord(
                **{
                    **memory,
                    "scope_type": "session",
                    "scope_id": session_id,
                    "paper_id": paper_id,
                    "updated_at": self._now(),
                }
            )
            if hasattr(self.repo, "save_scoped_memory"):
                self.repo.save_scoped_memory(self.session_scope(session_id), record.model_dump())
            return record.model_dump()
        recent_questions = [*memory.get("recent_questions", []), question][-8:]
        prior_summary = memory.get("conversation_summary", "")
        answer_preview = " ".join(answer.split())[:240]
        if prior_summary:
            summary = f"{prior_summary}\n- Q: {question}\n- A: {answer_preview}"
        else:
            summary = f"- Q: {question}\n- A: {answer_preview}"
        turn_summary = f"Q: {question} | A: {answer_preview}"[:320]
        active_topics = memory.get("active_topics", [])
        for topic in self._infer_topic_hints(question, overview):
            active_topics = self._append_unique(active_topics, topic, 6)
        record = SessionMemoryRecord(
            **{
                **memory,
                "scope_type": "session",
                "scope_id": session_id,
                "paper_id": paper_id,
                "conversation_summary": summary[-4000:],
                "recent_questions": recent_questions,
                "recent_turn_summaries": [*(memory.get("recent_turn_summaries", [])), turn_summary][-6:],
                "active_topics": active_topics,
                "updated_at": self._now(),
            }
        )
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self.session_scope(session_id), record.model_dump())
        return record.model_dump()

    def build_write_decision(
        self,
        paper_id: str,
        session_id: str,
        question: str,
        answer: str,
        overview: dict | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        stripped_question = question.strip()
        if self._looks_like_low_signal(stripped_question):
            decision = MemoryWriteDecision(
                should_write=False,
                reason="low_signal_turn",
                writes=[],
            )
            logger.info(
                "memory.write decision: should_write=false reason=%s session=%s paper=%s",
                decision.reason,
                session_id,
                paper_id,
            )
            return decision.model_dump()

        writes: list[MemoryWriteAction] = []
        concepts = self._extract_concepts(question)
        method_question = self._looks_like_method_question(question)
        experiment_question = self._looks_like_experiment_question(question)
        comparison_question = self._looks_like_comparison(question)
        confusion = self._looks_like_confusion(question)
        mastery = self._looks_like_mastery(question)

        for concept in concepts[:4]:
            writes.append(
                MemoryWriteAction(
                    target_scope=self.paper_scope(paper_id),
                    memory_type="concept_seen",
                    payload={"concept": concept},
                    confidence=0.62,
                )
            )

        if confusion:
            for concept in concepts[:2] or ["当前概念"]:
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.paper_scope(paper_id),
                        memory_type="stuck_point",
                        payload={"concept": concept, "question": question},
                        confidence=0.9,
                    )
                )
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.user_scope(user_id),
                        memory_type="weak_concept",
                        payload={"concept": concept},
                        confidence=0.82,
                    )
                )

        if method_question and overview and overview.get("method_summary"):
            writes.append(
                MemoryWriteAction(
                    target_scope=self.paper_scope(paper_id),
                    memory_type="method_summary",
                    payload={"summary": overview["method_summary"]},
                    confidence=0.88,
                )
            )
            takeaway = (overview.get("main_contributions") or [overview.get("conclusion", "")])[0]
            if takeaway:
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.paper_scope(paper_id),
                        memory_type="important_takeaway",
                        payload={"takeaway": takeaway},
                        confidence=0.74,
                    )
                )

        if experiment_question and overview:
            for item in overview.get("main_experiments", [])[:2]:
                takeaway = item.get("what_it_proves") or item.get("claim") or ""
                if takeaway:
                    writes.append(
                        MemoryWriteAction(
                            target_scope=self.paper_scope(paper_id),
                            memory_type="experiment_takeaway",
                            payload={"takeaway": takeaway},
                            confidence=0.84,
                        )
                    )

        if comparison_question and overview:
            for item in overview.get("recommended_readings", [])[:2]:
                title = item.get("title", "")
                relation = item.get("relation_to_current_paper", "related")
                if not title:
                    continue
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.paper_scope(paper_id),
                        memory_type="linked_paper",
                        payload={
                            "paper_id": f"ext:{title}",
                            "paper_title": title,
                            "relation": relation,
                        },
                        confidence=0.86,
                    )
                )
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.user_scope(user_id),
                        memory_type="cross_paper_link",
                        payload={
                            "source_paper_id": paper_id,
                            "target_paper_id": f"ext:{title}",
                            "relation": relation,
                        },
                        confidence=0.76,
                    )
                )

        if mastery:
            for concept in concepts[:2]:
                writes.append(
                    MemoryWriteAction(
                        target_scope=self.user_scope(user_id),
                        memory_type="mastered_concept",
                        payload={"concept": concept},
                        confidence=0.8,
                    )
                )

        topic_hints = self._infer_topic_hints(question, overview)
        for topic in topic_hints[:2]:
            writes.append(
                MemoryWriteAction(
                    target_scope=self.user_scope(user_id),
                    memory_type="topic_interest",
                    payload={"topic": topic},
                    confidence=0.66,
                )
            )

        should_write = len(writes) > 0
        reason = None if should_write else "no_high_value_memory"
        decision = MemoryWriteDecision(
            should_write=should_write,
            reason=reason,
            writes=writes,
        )
        logger.info(
            "memory.write decision: should_write=%s reason=%s session=%s paper=%s writes=%s",
            decision.should_write,
            decision.reason,
            session_id,
            paper_id,
            [f"{item.target_scope}:{item.memory_type}:{item.confidence:.2f}" for item in decision.writes],
        )
        return decision.model_dump()

    def apply_write_decision(
        self,
        paper_id: str,
        session_id: str,
        decision: dict,
        user_id: str = DEFAULT_USER_ID,
        source_question: str | None = None,
        source_answer_preview: str | None = None,
    ) -> dict:
        if not decision.get("should_write"):
            logger.info(
                "memory.write apply: skipped session=%s paper=%s reason=%s",
                session_id,
                paper_id,
                decision.get("reason"),
            )
            return {"applied": [], "skipped": decision.get("reason")}

        applied: list[str] = []
        for raw_action in decision.get("writes", []):
            action = MemoryWriteAction(**raw_action)
            if action.confidence < 0.55:
                logger.info(
                    "memory.write apply: dropped_low_confidence scope=%s type=%s confidence=%.2f",
                    action.target_scope,
                    action.memory_type,
                    action.confidence,
                )
                continue
            if action.target_scope.startswith("paper:"):
                changed = self._apply_paper_write_action(paper_id, action)
            elif action.target_scope.startswith("user:"):
                changed = self._apply_user_write_action(user_id, action)
            else:
                logger.info(
                    "memory.write apply: skipped_unknown_scope scope=%s type=%s",
                    action.target_scope,
                    action.memory_type,
                )
                continue
            applied.append(f"{action.target_scope}:{action.memory_type}")
            if changed and hasattr(self.repo, "save_memory_item_meta"):
                memory_id = self._build_memory_item_id(action.target_scope, action.memory_type, action.payload)
                self.repo.save_memory_item_meta(
                    memory_id,
                    {
                        "memory_id": memory_id,
                        "scope": action.target_scope,
                        "memory_type": action.memory_type,
                        "paper_id": paper_id if action.target_scope.startswith(("paper:", "session:")) else None,
                        "write_reason": decision.get("reason") or action.memory_type,
                        "write_confidence": action.confidence,
                        "source_question": source_question,
                        "source_answer_preview": (source_answer_preview or "")[:280],
                        "created_at": self._now(),
                        "updated_at": self._now(),
                    },
                )

        logger.info(
            "memory.write apply: session=%s paper=%s applied=%s",
            session_id,
            paper_id,
            applied,
        )
        return {"applied": applied, "skipped": None}

    def _apply_paper_write_action(self, paper_id: str, action: MemoryWriteAction) -> bool:
        memory = self.get_paper_memory(paper_id)
        changed = False

        if action.memory_type == "stuck_point":
            concept = action.payload.get("concept", "").strip()
            updated = self._append_unique(memory.get("stuck_points", []), concept, 12)
            changed = updated != memory.get("stuck_points", [])
            memory["stuck_points"] = updated
        elif action.memory_type == "important_takeaway":
            takeaway = action.payload.get("takeaway", "").strip()
            updated = self._append_unique(memory.get("important_takeaways", []), takeaway, 8)
            changed = updated != memory.get("important_takeaways", [])
            memory["important_takeaways"] = updated
        elif action.memory_type == "method_summary":
            summary = action.payload.get("summary", "").strip()
            changed = bool(summary) and summary != memory.get("method_summary", "")
            if summary:
                memory["method_summary"] = summary
        elif action.memory_type == "experiment_takeaway":
            takeaway = action.payload.get("takeaway", "").strip()
            updated = self._append_unique(memory.get("experiment_takeaways", []), takeaway, 8)
            changed = updated != memory.get("experiment_takeaways", [])
            memory["experiment_takeaways"] = updated
        elif action.memory_type == "concept_seen":
            concept = action.payload.get("concept", "").strip()
            updated = self._append_unique(memory.get("concepts_seen", []), concept, 16)
            changed = updated != memory.get("concepts_seen", [])
            memory["concepts_seen"] = updated
        elif action.memory_type == "linked_paper":
            link = PaperLinkItem(**action.payload).model_dump()
            updated = self._append_unique_dict(memory.get("linked_papers", []), link, "paper_id", 8)
            changed = updated != memory.get("linked_papers", [])
            memory["linked_papers"] = updated

        if changed:
            record = PaperMemoryRecord(**memory)
            if hasattr(self.repo, "save_scoped_memory"):
                self.repo.save_scoped_memory(self.paper_scope(paper_id), record.model_dump())
            else:
                self.repo.save_memory(paper_id, record.model_dump())
        else:
            logger.info(
                "memory.write dedup: scope=%s type=%s",
                self.paper_scope(paper_id),
                action.memory_type,
            )
        return changed

    def _apply_user_write_action(self, user_id: str, action: MemoryWriteAction) -> bool:
        memory = self.get_user_memory(user_id)
        changed = False

        if action.memory_type == "weak_concept":
            concept = action.payload.get("concept", "").strip()
            updated = self._append_unique(memory.get("weak_concepts", []), concept, 12)
            changed = updated != memory.get("weak_concepts", [])
            memory["weak_concepts"] = updated
        elif action.memory_type == "mastered_concept":
            concept = action.payload.get("concept", "").strip()
            updated = self._append_unique(memory.get("mastered_concepts", []), concept, 12)
            changed = updated != memory.get("mastered_concepts", [])
            memory["mastered_concepts"] = updated
            memory["weak_concepts"] = [item for item in memory.get("weak_concepts", []) if item != concept]
        elif action.memory_type == "cross_paper_link":
            link = CrossPaperLinkItem(**action.payload).model_dump()
            updated = self._append_unique_dict(memory.get("cross_paper_links", []), link, "target_paper_id", 12)
            changed = updated != memory.get("cross_paper_links", [])
            memory["cross_paper_links"] = updated
        elif action.memory_type == "topic_interest":
            topic = action.payload.get("topic", "").strip()
            updated = self._append_unique(memory.get("recent_topics", []), topic, 8)
            changed = updated != memory.get("recent_topics", [])
            memory["recent_topics"] = updated
        elif action.memory_type == "explanation_preference":
            preference = action.payload.get("preferred_explanation_style", "").strip()
            changed = bool(preference) and preference != memory.get("preferred_explanation_style", "")
            if preference:
                memory["preferred_explanation_style"] = preference

        if changed and hasattr(self.repo, "save_scoped_memory"):
            record = UserMemoryRecord(**memory)
            self.repo.save_scoped_memory(self.user_scope(user_id), record.model_dump())
        elif not changed:
            logger.info(
                "memory.write dedup: scope=%s type=%s",
                self.user_scope(user_id),
                action.memory_type,
            )
        return changed

    def update_paper_memory_from_question(self, paper_id: str, question: str, overview: dict | None = None) -> dict:
        memory = self.get_paper_memory(paper_id=paper_id)
        key_questions = memory.get("key_questions", [])
        if question not in key_questions:
            key_questions = [*key_questions, question][-8:]

        concepts_seen = memory.get("concepts_seen", [])
        for concept in self._extract_concepts(question):
            concepts_seen = self._append_unique(concepts_seen, concept, 16)

        stuck_points = memory.get("stuck_points", [])
        if self._looks_like_confusion(question):
            for concept in self._extract_concepts(question) or ["当前概念"]:
                stuck_points = self._append_unique(stuck_points, concept, 12)

        method_summary = memory.get("method_summary", "")
        if overview and any(token in question.lower() for token in ["方法", "模块", "设计", "why", "how", "loss"]):
            method_summary = overview.get("method_summary", method_summary)

        experiment_takeaways = memory.get("experiment_takeaways", [])
        if overview and any(token in question.lower() for token in ["实验", "ablation", "baseline", "result", "对比"]):
            for item in overview.get("main_experiments", [])[:3]:
                takeaway = item.get("what_it_proves") or item.get("claim") or ""
                if takeaway:
                    experiment_takeaways = self._append_unique(experiment_takeaways, takeaway, 8)

        linked_papers = memory.get("linked_papers", [])
        if overview and any(token in question for token in ["对比", "区别", "相比", "baseline"]):
            for item in overview.get("recommended_readings", [])[:2]:
                paper_title = item.get("title", "")
                if not paper_title:
                    continue
                linked_papers = self._append_unique_dict(
                    linked_papers,
                    PaperLinkItem(
                        paper_id=f"ext:{paper_title}",
                        paper_title=paper_title,
                        relation=item.get("relation_to_current_paper", "related"),
                    ).model_dump(),
                    "paper_id",
                    8,
                )

        record = PaperMemoryRecord(
            **{
                **memory,
                "scope_type": "paper",
                "scope_id": paper_id,
                "paper_id": paper_id,
                "key_questions": key_questions,
                "stuck_points": stuck_points,
                "method_summary": method_summary,
                "experiment_takeaways": experiment_takeaways,
                "concepts_seen": concepts_seen,
                "linked_papers": linked_papers,
            }
        )
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self.paper_scope(paper_id), record.model_dump())
        else:
            self.repo.save_memory(paper_id, record.model_dump())
        return record.model_dump()

    def initialize_paper_memory_from_overview(self, paper_id: str, overview: dict) -> dict:
        memory = self.get_paper_memory(paper_id)
        important_takeaways = memory.get("important_takeaways", [])
        for item in overview.get("main_contributions", [])[:3]:
            important_takeaways = self._append_unique(important_takeaways, item, 8)
        conclusion = overview.get("conclusion", "")
        if conclusion:
            important_takeaways = self._append_unique(important_takeaways, conclusion, 8)

        experiment_takeaways = memory.get("experiment_takeaways", [])
        for item in overview.get("main_experiments", [])[:3]:
            takeaway = item.get("what_it_proves") or item.get("claim") or ""
            if takeaway:
                experiment_takeaways = self._append_unique(experiment_takeaways, takeaway, 8)

        concepts_seen = memory.get("concepts_seen", [])
        for topic in [item.get("topic", "") for item in overview.get("prerequisite_knowledge", [])]:
            concepts_seen = self._append_unique(concepts_seen, topic, 16)

        linked_papers = memory.get("linked_papers", [])
        for item in overview.get("recommended_readings", [])[:3]:
            title = item.get("title", "")
            if not title:
                continue
            linked_papers = self._append_unique_dict(
                linked_papers,
                PaperLinkItem(
                    paper_id=f"ext:{title}",
                    paper_title=title,
                    relation=item.get("relation_to_current_paper", "recommended"),
                ).model_dump(),
                "paper_id",
                8,
            )

        record = PaperMemoryRecord(
            **{
                **memory,
                "scope_type": "paper",
                "scope_id": paper_id,
                "paper_id": paper_id,
                "important_takeaways": important_takeaways,
                "method_summary": overview.get("method_summary", memory.get("method_summary", "")),
                "experiment_takeaways": experiment_takeaways,
                "concepts_seen": concepts_seen,
                "linked_papers": linked_papers,
            }
        )
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self.paper_scope(paper_id), record.model_dump())
        else:
            self.repo.save_memory(paper_id, record.model_dump())
        return record.model_dump()

    def update_user_memory_from_ingestion(
        self,
        paper_id: str,
        overview: dict | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        memory = self.get_user_memory(user_id)
        read_paper_ids = memory.get("read_paper_ids", [])
        if paper_id not in read_paper_ids:
            read_paper_ids = [*read_paper_ids, paper_id]

        recent_topics = memory.get("recent_topics", [])
        title = ""
        paper = self.repo.get_paper(paper_id)
        if paper:
            title = self._safe_string(paper.get("title"))
        for topic in self._infer_topic_hints(title, overview):
            recent_topics = self._append_unique(recent_topics, topic, 8)

        paper_link_candidates = memory.get("paper_link_candidates", [])
        for candidate in self._infer_paper_link_candidates(paper_id, overview):
            paper_link_candidates = self._append_unique_dict(
                paper_link_candidates,
                candidate,
                "target_paper_id",
                12,
            )

        record = UserMemoryRecord(
            **{
                **memory,
                "scope_type": "user",
                "scope_id": user_id,
                "user_id": user_id,
                "read_paper_ids": read_paper_ids,
                "recent_topics": recent_topics,
                "paper_link_candidates": paper_link_candidates,
            }
        )
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self.user_scope(user_id), record.model_dump())
        return record.model_dump()

    def update_user_memory_from_conversation(
        self,
        question: str,
        answer: str | None = None,
        paper_id: str | None = None,
        overview: dict | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        memory = self.get_user_memory(user_id)

        weak_concepts = memory.get("weak_concepts", [])
        if self._looks_like_confusion(question):
            for concept in self._extract_concepts(question) or ["当前概念"]:
                weak_concepts = self._append_unique(weak_concepts, concept, 12)

        mastered_concepts = memory.get("mastered_concepts", [])
        if self._looks_like_mastery(question):
            for concept in self._extract_concepts(question):
                mastered_concepts = self._append_unique(mastered_concepts, concept, 12)
                weak_concepts = [item for item in weak_concepts if item != concept]

        preferred_explanation_style = memory.get("preferred_explanation_style", "intuitive_then_formula")
        inferred_style = self._infer_explanation_style(question, answer)
        if inferred_style:
            preferred_explanation_style = inferred_style

        cross_paper_links = memory.get("cross_paper_links", [])
        if paper_id and overview and any(token in question for token in ["对比", "区别", "相比", "联系", "compare"]):
            for candidate in self._infer_paper_link_candidates(paper_id, overview)[:2]:
                cross_paper_links = self._append_unique_dict(
                    cross_paper_links,
                    candidate,
                    "target_paper_id",
                    12,
                )

        record = UserMemoryRecord(
            **{
                **memory,
                "scope_type": "user",
                "scope_id": user_id,
                "user_id": user_id,
                "weak_concepts": weak_concepts,
                "mastered_concepts": mastered_concepts,
                "preferred_explanation_style": preferred_explanation_style,
                "cross_paper_links": cross_paper_links,
            }
        )
        if hasattr(self.repo, "save_scoped_memory"):
            self.repo.save_scoped_memory(self.user_scope(user_id), record.model_dump())
        return record.model_dump()

    def update_user_memory(
        self,
        paper_id: str,
        question: str,
        overview: dict | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        return self.update_user_memory_from_conversation(
            paper_id=paper_id,
            question=question,
            answer=None,
            overview=overview,
            user_id=user_id,
        )
