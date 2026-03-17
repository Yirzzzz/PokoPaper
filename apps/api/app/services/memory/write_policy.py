from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from app.schemas.memory import MemoryWriteAction, MemoryWriteDecision

WRITE_CONFIDENCE_THRESHOLD = 0.68
LOW_SIGNAL_EXACT = {
    "你好",
    "您好",
    "hi",
    "hello",
    "谢谢",
    "thanks",
    "thank you",
    "继续",
    "展开一点",
    "再说一遍",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _append_unique(items: list[str], value: str, limit: int) -> list[str]:
    normalized = value.strip()
    if not normalized:
        return items[-limit:]
    merged = [item for item in items if item != normalized]
    merged.append(normalized)
    return merged[-limit:]


def _is_low_signal(text: str) -> bool:
    normalized = text.strip().lower()
    return not normalized or normalized in LOW_SIGNAL_EXACT or len(normalized) <= 2


def _extract_concepts(text: str) -> list[str]:
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9\-\+]{2,}", text)
    results: list[str] = []
    for candidate in candidates:
        lowered = candidate.lower()
        if lowered in {"what", "why", "how", "this", "that", "with", "from", "into", "then"}:
            continue
        if candidate not in results:
            results.append(candidate)
        if len(results) == 6:
            break
    return results


def _extract_overview_keywords(overview: dict[str, Any] | None) -> list[str]:
    if not overview:
        return []
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


def _looks_like_confusion(text: str) -> bool:
    lowered = text.lower()
    return any(token in text for token in ["没懂", "不理解", "看不懂", "困惑", "不太明白", "什么意思"]) or "what is" in lowered


def _looks_like_mastery(text: str) -> bool:
    return any(token in text for token in ["我懂了", "我明白了", "理解了", "掌握了", "已经会了"])


def _infer_style_preference(question: str) -> tuple[str | None, bool]:
    explicit_markers = ["以后都", "之后都", "默认", "一直", "都先", "先讲"]
    if "先讲直觉再讲公式" in question or "先讲直觉，再讲公式" in question:
        return "intuitive_then_formula", any(marker in question for marker in explicit_markers)
    if "多举例" in question or "先举例" in question or "先讲例子" in question:
        return "intuitive_with_examples", any(marker in question for marker in explicit_markers)
    if "通俗举例" in question or "通俗一点" in question or "举个例子" in question:
        return "intuitive_with_examples", False
    if "直接讲公式" in question or "先讲公式" in question:
        return "formula_first", any(marker in question for marker in explicit_markers)
    return None, False


def _make_action(
    *,
    target_scope: str,
    target_field: str,
    operation: str,
    value: Any,
    reason: str,
    confidence: float,
    evidence_count: int,
    source_type: str,
    memory_type: str,
    payload: dict[str, Any],
) -> MemoryWriteAction:
    return MemoryWriteAction(
        target_scope=target_scope,
        target_field=target_field,
        operation=operation if confidence >= WRITE_CONFIDENCE_THRESHOLD else "ignore",
        value=value,
        reason=reason,
        confidence=round(confidence, 2),
        evidence_count=evidence_count,
        source_type=source_type,
        last_updated_at=_now(),
        memory_type=memory_type,
        payload=payload,
    )


def _topic_candidates_from_dialog(question: str, overview: dict[str, Any] | None) -> list[str]:
    topics: list[str] = []
    for topic in _extract_concepts(question)[:3]:
        if topic not in topics:
            topics.append(topic)
    for topic in _extract_overview_keywords(overview)[:2]:
        if topic not in topics:
            topics.append(topic)
    return topics[:4]


def decide_memory_writes(
    *,
    source_type: str,
    session_id: str | None = None,
    paper_id: str | None = None,
    user_id: str = "local-user",
    question: str = "",
    answer: str | None = None,
    overview: dict[str, Any] | None = None,
    existing_user_memory: dict[str, Any] | None = None,
    existing_paper_memory: dict[str, Any] | None = None,
    existing_conversation_memory: dict[str, Any] | None = None,
) -> MemoryWriteDecision:
    now = _now()
    existing_user_memory = existing_user_memory or {}
    existing_paper_memory = existing_paper_memory or {}
    existing_conversation_memory = existing_conversation_memory or {}

    if source_type == "dialog" and _is_low_signal(question):
        return MemoryWriteDecision(should_write=False, reason="low_signal_turn", threshold=WRITE_CONFIDENCE_THRESHOLD, writes=[])

    actions: list[MemoryWriteAction] = []

    if source_type in {"dialog", "summary"}:
        actions.extend(
            _dialog_write_candidates(
                session_id=session_id,
                paper_id=paper_id,
                user_id=user_id,
                question=question,
                answer=answer or "",
                overview=overview,
                existing_user_memory=existing_user_memory,
                existing_conversation_memory=existing_conversation_memory,
            )
        )

    if source_type in {"upload", "overview"}:
        actions.extend(
            _ingestion_write_candidates(
                paper_id=paper_id,
                user_id=user_id,
                overview=overview,
                existing_user_memory=existing_user_memory,
                existing_paper_memory=existing_paper_memory,
            )
        )

    should_write = any(action.operation != "ignore" for action in actions)
    reason = None if should_write else "below_threshold_or_no_high_value_memory"
    normalized_actions = [
        action.model_copy(update={"last_updated_at": now})
        for action in actions
    ]
    return MemoryWriteDecision(
        should_write=should_write,
        reason=reason,
        threshold=WRITE_CONFIDENCE_THRESHOLD,
        writes=normalized_actions,
    )


def _dialog_write_candidates(
    *,
    session_id: str | None,
    paper_id: str | None,
    user_id: str,
    question: str,
    answer: str,
    overview: dict[str, Any] | None,
    existing_user_memory: dict[str, Any],
    existing_conversation_memory: dict[str, Any],
) -> list[MemoryWriteAction]:
    actions: list[MemoryWriteAction] = []
    concepts = _extract_concepts(question)
    topic_candidates = _topic_candidates_from_dialog(question, overview)

    if session_id and topic_candidates:
        actions.append(
            _make_action(
                target_scope="conversation",
                target_field="active_topics",
                operation="merge",
                value=topic_candidates[:2],
                reason="当前问题中出现了可复用的讨论主题，适合作为当前会话 active topics。",
                confidence=0.74,
                evidence_count=len(topic_candidates[:2]),
                source_type="dialog",
                memory_type="active_topic",
                payload={"topics": topic_candidates[:2], "session_id": session_id},
            )
        )

    if session_id and answer.strip() and not _is_low_signal(question):
        answer_preview = " ".join(answer.split())[:180]
        actions.append(
            _make_action(
                target_scope="conversation",
                target_field="conversation_summary",
                operation="update",
                value=f"Q: {question.strip()} | A: {answer_preview}",
                reason="当前轮问答信息量较高，可生成一个会话级短摘要供调试或后续压缩使用。",
                confidence=0.72,
                evidence_count=2,
                source_type="dialog",
                memory_type="conversation_summary",
                payload={"summary": f"Q: {question.strip()} | A: {answer_preview}", "session_id": session_id},
            )
        )

    if _looks_like_confusion(question):
        for concept in concepts[:2]:
            repeat_bonus = 0.1 if concept in existing_user_memory.get("weak_concepts", []) else 0.0
            actions.append(
                _make_action(
                    target_scope="user",
                    target_field="weak_concepts",
                    operation="append",
                    value=concept,
                    reason="用户明确表达了困惑，且概念可被稳定识别，适合写入用户层 weak concepts。",
                    confidence=0.74 + repeat_bonus,
                    evidence_count=1 + int(repeat_bonus > 0),
                    source_type="dialog",
                    memory_type="weak_concept",
                    payload={"concept": concept},
                )
            )

    if _looks_like_mastery(question):
        for concept in concepts[:2]:
            repeat_bonus = 0.08 if concept in existing_user_memory.get("weak_concepts", []) else 0.0
            actions.append(
                _make_action(
                    target_scope="user",
                    target_field="mastered_concepts",
                    operation="append",
                    value=concept,
                    reason="用户明确表达已理解该概念，适合写入 mastered concepts，并与 weak concepts 做冲突处理。",
                    confidence=0.78 + repeat_bonus,
                    evidence_count=1 + int(repeat_bonus > 0),
                    source_type="dialog",
                    memory_type="mastered_concept",
                    payload={"concept": concept},
                )
            )

    inferred_style, explicit = _infer_style_preference(question)
    if inferred_style:
        actions.append(
            _make_action(
                target_scope="user",
                target_field="preferred_explanation_style",
                operation="update",
                value=inferred_style,
                reason="用户对解释风格给出了稳定偏好表达，适合更新长期 explanation style。",
                confidence=0.9 if explicit else 0.56,
                evidence_count=2 if explicit else 1,
                source_type="dialog",
                memory_type="explanation_preference",
                payload={"preferred_explanation_style": inferred_style},
            )
        )

    for topic in topic_candidates[:2]:
        confidence = 0.71 if topic in existing_user_memory.get("recent_topics", []) else 0.63
        actions.append(
            _make_action(
                target_scope="user",
                target_field="recent_topics",
                operation="merge",
                value=topic,
                reason="当前问题涉及的主题对长期阅读画像有一定价值，但对话侧置信度低于上传侧。",
                confidence=confidence,
                evidence_count=1 + int(topic in existing_user_memory.get("recent_topics", [])),
                source_type="dialog",
                memory_type="topic_interest",
                payload={"topic": topic},
            )
        )

    if paper_id and overview and any(token in question for token in ["对比", "区别", "相比", "联系", "compare"]):
        for item in overview.get("recommended_readings", [])[:1]:
            title = (item.get("title") or "").strip()
            relation = (item.get("relation_to_current_paper") or "related").strip()
            if not title:
                continue
            actions.append(
                _make_action(
                    target_scope="user",
                    target_field="cross_paper_links",
                    operation="merge",
                    value={
                        "source_paper_id": paper_id,
                        "target_paper_id": f"ext:{title}",
                        "relation": relation,
                    },
                    reason="用户明确发起跨论文比较，且 overview 给出了推荐关联论文，适合作为 confirmed cross-paper link。",
                    confidence=0.78,
                    evidence_count=2,
                    source_type="dialog",
                    memory_type="cross_paper_link",
                    payload={
                        "source_paper_id": paper_id,
                        "target_paper_id": f"ext:{title}",
                        "relation": relation,
                    },
                )
            )

    if paper_id and overview and any(token in question for token in ["方法", "模块", "实验", "结果", "动机", "为什么"]):
        if overview.get("research_motivation"):
            actions.append(
                _make_action(
                    target_scope="paper",
                    target_field="motivation",
                    operation="update",
                    value=overview.get("research_motivation", ""),
                    reason="当前对话明确围绕当前论文展开，可把已知 overview 中的动机写入 paper memory。",
                    confidence=0.73,
                    evidence_count=2,
                    source_type="dialog",
                    memory_type="motivation",
                    payload={"value": overview.get("research_motivation", ""), "paper_id": paper_id},
                )
            )
        if overview.get("method_summary"):
            actions.append(
                _make_action(
                    target_scope="paper",
                    target_field="method",
                    operation="update",
                    value=overview.get("method_summary", ""),
                    reason="当前问题和论文方法强相关，适合将方法主线稳定写入 paper memory。",
                    confidence=0.76,
                    evidence_count=2,
                    source_type="dialog",
                    memory_type="method",
                    payload={"value": overview.get("method_summary", ""), "paper_id": paper_id},
                )
            )
        result = ""
        for item in overview.get("main_experiments", [])[:1]:
            result = (item.get("claim") or item.get("what_it_proves") or "").strip()
        if result:
            actions.append(
                _make_action(
                    target_scope="paper",
                    target_field="key_results",
                    operation="update",
                    value=result,
                    reason="当前问题触发了论文实验/结果相关上下文，适合补充 paper key results。",
                    confidence=0.72,
                    evidence_count=2,
                    source_type="dialog",
                    memory_type="key_results",
                    payload={"value": result, "paper_id": paper_id},
                )
            )

    return actions


def _ingestion_write_candidates(
    *,
    paper_id: str | None,
    user_id: str,
    overview: dict[str, Any] | None,
    existing_user_memory: dict[str, Any],
    existing_paper_memory: dict[str, Any],
) -> list[MemoryWriteAction]:
    actions: list[MemoryWriteAction] = []
    if not paper_id or not overview:
        return actions

    motivation = (overview.get("research_motivation") or "").strip()
    if motivation:
        actions.append(
            _make_action(
                target_scope="paper",
                target_field="motivation",
                operation="update",
                value=motivation,
                reason="论文 overview 提供了直接动机描述，属于高置信 paper memory。",
                confidence=0.93,
                evidence_count=2,
                source_type="overview",
                memory_type="motivation",
                payload={"value": motivation, "paper_id": paper_id},
            )
        )

    method = (overview.get("method_summary") or "").strip()
    if method:
        actions.append(
            _make_action(
                target_scope="paper",
                target_field="method",
                operation="update",
                value=method,
                reason="论文 overview 提供了明确方法主线，适合高置信写入 paper method。",
                confidence=0.94,
                evidence_count=2,
                source_type="overview",
                memory_type="method",
                payload={"value": method, "paper_id": paper_id},
            )
        )

    key_result = ""
    for item in overview.get("main_experiments", [])[:2]:
        candidate = (item.get("claim") or item.get("what_it_proves") or "").strip()
        if candidate:
            key_result = candidate if not key_result else f"{key_result}；{candidate}"
    if key_result:
        actions.append(
            _make_action(
                target_scope="paper",
                target_field="key_results",
                operation="update",
                value=key_result,
                reason="overview 中包含实验结论，适合高置信写入 paper key results。",
                confidence=0.91,
                evidence_count=min(2, len(overview.get("main_experiments", []))),
                source_type="overview",
                memory_type="key_results",
                payload={"value": key_result, "paper_id": paper_id},
            )
        )

    keywords = _extract_overview_keywords(overview)
    if keywords:
        actions.append(
            _make_action(
                target_scope="paper",
                target_field="keywords",
                operation="merge",
                value=keywords,
                reason="从 prerequisite knowledge 和 key modules 中抽取关键词，适合形成 paper keywords。",
                confidence=0.88,
                evidence_count=len(keywords),
                source_type="overview",
                memory_type="keywords",
                payload={"keywords": keywords, "paper_id": paper_id},
            )
        )

    for topic in keywords[:2]:
        confidence = 0.84 if topic not in existing_user_memory.get("recent_topics", []) else 0.9
        actions.append(
            _make_action(
                target_scope="user",
                target_field="recent_topics",
                operation="merge",
                value=topic,
                reason="上传/解析阶段能够高置信反映用户最近阅读主题，适合写入 recent topics。",
                confidence=confidence,
                evidence_count=2,
                source_type="upload",
                memory_type="topic_interest",
                payload={"topic": topic},
            )
        )

    return actions
