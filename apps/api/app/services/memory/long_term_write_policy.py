from __future__ import annotations

import re
from typing import Any

from app.schemas.memory import LongTermMemoryWriteAction, LongTermMemoryWriteDecision

LONG_TERM_WRITE_THRESHOLD = 0.7
LOW_SIGNAL_EXACT = {
    "你好",
    "您好",
    "hi",
    "hello",
    "谢谢",
    "thank you",
    "thanks",
    "继续",
    "展开一点",
    "再说一遍",
}
LOW_SIGNAL_PREFIXES = ("继续", "再说", "展开", "举个例子", "详细说")


def _normalize_text(value: str | None) -> str:
    return (value or "").strip()


def _preview(text: str, limit: int = 180) -> str:
    return " ".join(text.split())[:limit]


def _confidence_level(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= LONG_TERM_WRITE_THRESHOLD:
        return "medium"
    return "low"


def _extract_concepts(text: str) -> list[str]:
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9\-\+]{2,}", text)
    concepts: list[str] = []
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered in {"what", "why", "how", "this", "that", "with", "from", "into"}:
            continue
        if candidate not in concepts:
            concepts.append(candidate)
        if len(concepts) == 6:
            break
    return concepts


def _recent_texts(recent_messages: list[dict[str, Any]]) -> list[str]:
    return [_normalize_text(message.get("content_md") or "") for message in recent_messages if _normalize_text(message.get("content_md"))]


def _count_concept_repetition(concept: str, recent_messages: list[dict[str, Any]], current_text: str) -> int:
    texts = [* _recent_texts(recent_messages), current_text]
    lowered_concept = concept.lower()
    return sum(1 for text in texts if lowered_concept in text.lower())


def _looks_like_low_signal(question: str) -> bool:
    normalized = _normalize_text(question).lower()
    if not normalized:
        return True
    if normalized in LOW_SIGNAL_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in LOW_SIGNAL_PREFIXES):
        return True
    return len(normalized) <= 3


def _detect_confusion_signals(question: str) -> list[str]:
    markers = ["没看懂", "没懂", "不理解", "什么意思", "有什么区别", "为什么这样设计", "为什么这么设计", "怎么理解"]
    return [marker for marker in markers if marker in question]


def _looks_like_method_turn(question: str, answer: str, source_scope: str) -> bool:
    lowered_question = question.lower()
    lowered_answer = answer.lower()
    if source_scope != "paper_chat":
        return False
    return any(token in question for token in ["方法", "怎么做", "主线", "设计"]) or any(
        token in lowered_question or token in lowered_answer
        for token in ["method", "architecture", "design", "pipeline"]
    )


def _looks_like_result_turn(question: str, answer: str, source_scope: str) -> bool:
    lowered_question = question.lower()
    lowered_answer = answer.lower()
    if source_scope != "paper_chat":
        return False
    return any(token in question for token in ["实验", "结果", "结论", "对比", "消融"]) or any(
        token in lowered_question or token in lowered_answer
        for token in ["experiment", "result", "finding", "ablation", "baseline"]
    )


def _looks_like_cross_paper_turn(question: str, answer: str) -> bool:
    lowered_question = question.lower()
    lowered_answer = answer.lower()
    return any(token in question for token in ["区别", "对比", "相比", "联系"]) or any(
        token in lowered_question or token in lowered_answer
        for token in ["compare", "difference", "similar", "relation"]
    )


def _make_action(
    *,
    memory_type: str,
    memory_text: str,
    source_type: str,
    source_scope: str,
    conversation_id: str,
    paper_id: str | None,
    confidence: float,
    reason: str,
    evidence_count: int,
    concepts: list[str] | None = None,
    trigger_signals: list[str] | None = None,
    question: str = "",
    answer: str = "",
    related_papers: list[str] | None = None,
) -> LongTermMemoryWriteAction | None:
    if confidence < LONG_TERM_WRITE_THRESHOLD:
        return None
    return LongTermMemoryWriteAction(
        memory_type=memory_type,
        memory_text=memory_text,
        source_type=source_type,
        source_scope=source_scope,
        conversation_id=conversation_id,
        paper_id=paper_id,
        confidence=round(confidence, 2),
        metadata={
            "reason": reason,
            "evidence_count": evidence_count,
            "confidence_level": _confidence_level(confidence),
            "concepts": concepts or [],
            "trigger_signals": trigger_signals or [],
            "related_papers": related_papers or [],
            "question_preview": _preview(question),
            "answer_preview": _preview(answer),
        },
    )


def decide_long_term_memory_writes(
    *,
    source_type: str,
    source_scope: str,
    conversation_id: str,
    paper_id: str | None,
    question: str,
    answer: str,
    recent_messages: list[dict[str, Any]] | None = None,
) -> LongTermMemoryWriteDecision:
    normalized_question = _normalize_text(question)
    normalized_answer = _normalize_text(answer)
    recent_messages = recent_messages or []

    if source_type != "dialog":
        return LongTermMemoryWriteDecision(should_write=False, reason="unsupported_source_type", writes=[])

    if _looks_like_low_signal(normalized_question):
        return LongTermMemoryWriteDecision(should_write=False, reason="low_signal_turn", writes=[])

    current_text = f"{normalized_question}\n{normalized_answer}".strip()
    concepts = _extract_concepts(current_text)
    writes: list[LongTermMemoryWriteAction] = []

    confusion_signals = _detect_confusion_signals(normalized_question)
    if confusion_signals:
        key_concepts = concepts[:2]
        repetition = max((_count_concept_repetition(concept, recent_messages, current_text) for concept in key_concepts), default=1)
        confidence = min(0.78 + max(repetition - 1, 0) * 0.07, 0.93)
        candidate = _make_action(
            memory_type="concept_confusion",
            memory_text=f"用户在当前会话中对 {', '.join(key_concepts) if key_concepts else '当前概念'} 表达困惑：{_preview(normalized_question, 220)}",
            source_type=source_type,
            source_scope=source_scope,
            conversation_id=conversation_id,
            paper_id=paper_id,
            confidence=confidence,
            reason="用户明确表达困惑，且该信息对后续长期 recall 有价值。",
            evidence_count=max(repetition, 1),
            concepts=key_concepts,
            trigger_signals=confusion_signals,
            question=normalized_question,
            answer=normalized_answer,
        )
        if candidate is not None:
            writes.append(candidate)

    if _looks_like_method_turn(normalized_question, normalized_answer, source_scope):
        method_concepts = concepts[:3]
        repetition = max((_count_concept_repetition(concept, recent_messages, current_text) for concept in method_concepts), default=1)
        confidence = min(0.82 + max(repetition - 1, 0) * 0.05, 0.94)
        candidate = _make_action(
            memory_type="method_summary",
            memory_text=f"当前论文的方法主线可总结为：{_preview(normalized_answer or normalized_question, 240)}",
            source_type=source_type,
            source_scope=source_scope,
            conversation_id=conversation_id,
            paper_id=paper_id,
            confidence=confidence,
            reason="当前轮形成了相对稳定的方法主线信息，适合作为长期记忆候选。",
            evidence_count=max(repetition, 1),
            concepts=method_concepts,
            trigger_signals=["method_turn"],
            question=normalized_question,
            answer=normalized_answer,
        )
        if candidate is not None:
            writes.append(candidate)

    if _looks_like_result_turn(normalized_question, normalized_answer, source_scope):
        result_concepts = concepts[:3]
        candidate = _make_action(
            memory_type="experiment_finding",
            memory_text=f"当前论文的关键实验/结果信息：{_preview(normalized_answer or normalized_question, 240)}",
            source_type=source_type,
            source_scope=source_scope,
            conversation_id=conversation_id,
            paper_id=paper_id,
            confidence=0.84,
            reason="当前轮包含明确实验结论或结果总结，适合作为长期记忆候选。",
            evidence_count=1,
            concepts=result_concepts,
            trigger_signals=["result_turn"],
            question=normalized_question,
            answer=normalized_answer,
        )
        if candidate is not None:
            writes.append(candidate)

    if _looks_like_cross_paper_turn(normalized_question, normalized_answer):
        related_concepts = concepts[:3]
        candidate = _make_action(
            memory_type="cross_paper_link",
            memory_text=f"当前会话中形成了明确的跨论文/跨方法关联：{_preview(normalized_question or normalized_answer, 220)}",
            source_type=source_type,
            source_scope=source_scope,
            conversation_id=conversation_id,
            paper_id=paper_id,
            confidence=0.79 if len(related_concepts) >= 2 else 0.72,
            reason="当前轮明确在比较或关联两个方法/论文，适合作为统一长期记忆候选。",
            evidence_count=2 if len(related_concepts) >= 2 else 1,
            concepts=related_concepts,
            trigger_signals=["cross_paper_turn"],
            question=normalized_question,
            answer=normalized_answer,
            related_papers=related_concepts[:2],
        )
        if candidate is not None:
            writes.append(candidate)

    if not writes:
        return LongTermMemoryWriteDecision(should_write=False, reason="no_high_value_long_term_candidate", writes=[])
    return LongTermMemoryWriteDecision(should_write=True, reason=None, writes=writes)
