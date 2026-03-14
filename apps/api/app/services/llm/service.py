from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.prompts.paper_analysis_prompt import (
    build_agent_answer_prompt,
    build_global_agent_answer_prompt_with_context,
    build_paper_analysis_prompt,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.last_debug_info: dict[str, Any] | None = None

    def list_models(self) -> list[dict[str, Any]]:
        catalog = [
            {
                "id": self._build_model_id("modelscope", settings.modelscope_model),
                "label": f"{settings.modelscope_model} · ModelScope",
                "provider": "modelscope",
                "model": settings.modelscope_model,
                "base_url": settings.modelscope_base_url,
                "enabled": bool(settings.modelscope_api_key),
                "supports_thinking": True,
            },
            {
                "id": self._build_model_id("dashscope", settings.dashscope_model),
                "label": f"{settings.dashscope_model} · DashScope",
                "provider": "dashscope",
                "model": settings.dashscope_model,
                "base_url": settings.dashscope_base_url,
                "enabled": bool(settings.dashscope_api_key and settings.dashscope_base_url),
                "supports_thinking": True,
            },
        ]
        return catalog

    def get_model_config(self, selected_model: str | None) -> dict[str, Any] | None:
        models = self.list_models()
        if selected_model:
            return next((item for item in models if item["id"] == selected_model and item["enabled"]), None)
        return next((item for item in models if item["enabled"]), None)

    def generate_grounded_answer(
        self,
        selected_model: str | None,
        question: str,
        overview: dict[str, Any],
        evidence_chunks: list[dict[str, Any]],
        conversation_context: dict[str, Any] | None = None,
        user_memory: dict[str, Any] | None = None,
        enable_thinking: bool | None = None,
    ) -> str | None:
        self.last_debug_info = None
        model_config = self.get_model_config(selected_model)
        if model_config is None:
            self.last_debug_info = {
                "stage": "answer",
                "status": "skipped",
                "reason": "no_enabled_external_model",
                "selected_model": selected_model,
            }
            logger.info("llm.answer skipped: no enabled external model, using fallback")
            return None

        try:
            from openai import OpenAI
        except ImportError:
            self.last_debug_info = {
                "stage": "answer",
                "status": "skipped",
                "reason": "openai_package_not_installed",
                "provider": model_config["provider"],
                "model": model_config["model"],
            }
            logger.warning("llm.answer skipped: openai package not installed")
            return None

        client = OpenAI(
            base_url=model_config["base_url"],
            api_key=self._get_api_key(model_config["provider"]),
        )
        try:
            extra_body = self._build_extra_body(
                provider=model_config["provider"],
                enable_thinking=enable_thinking,
                stream=True,
            )
            logger.info(
                "llm.answer request: provider=%s model=%s selected=%s",
                model_config["provider"],
                model_config["model"],
                selected_model,
            )
            self.last_debug_info = {
                "stage": "answer",
                "status": "requesting",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "extra_body": extra_body,
                "thinking_effective": bool(extra_body and extra_body.get("enable_thinking")),
            }
            content, reasoning = self._stream_completion(
                client=client,
                model=model_config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个论文陪读智能体。",
                    },
                    {
                        "role": "user",
                        "content": build_agent_answer_prompt(
                            question=question,
                            overview=overview,
                            evidence_chunks=evidence_chunks,
                            conversation_context=conversation_context,
                            user_memory=user_memory,
                        ),
                    },
                ],
                extra_body=extra_body,
            )
            logger.info(
                "llm.answer success: provider=%s model=%s has_content=%s has_reasoning=%s",
                model_config["provider"],
                model_config["model"],
                bool(content),
                bool(reasoning),
            )
            self.last_debug_info = {
                "stage": "answer",
                "status": "success",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "has_content": bool(content),
                "has_reasoning": bool(reasoning),
                "streaming_used": True,
            }
            return content
        except Exception as exc:
            self.last_debug_info = {
                "stage": "answer",
                "status": "failed",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            logger.exception(
                "llm.answer failed: provider=%s model=%s error=%s",
                model_config["provider"],
                model_config["model"],
                exc,
            )
            return None

    def generate_global_memory_answer(
        self,
        selected_model: str | None,
        question: str,
        conversation_context: dict[str, Any] | None = None,
        user_memory: dict[str, Any] | None = None,
        enable_thinking: bool | None = None,
    ) -> str | None:
        self.last_debug_info = None
        model_config = self.get_model_config(selected_model)
        if model_config is None:
            self.last_debug_info = {
                "stage": "global_answer",
                "status": "skipped",
                "reason": "no_enabled_external_model",
                "selected_model": selected_model,
            }
            logger.info("llm.global skipped: no enabled external model, using fallback")
            return None

        try:
            from openai import OpenAI
        except ImportError:
            self.last_debug_info = {
                "stage": "global_answer",
                "status": "skipped",
                "reason": "openai_package_not_installed",
                "provider": model_config["provider"],
                "model": model_config["model"],
            }
            logger.warning("llm.global skipped: openai package not installed")
            return None

        client = OpenAI(
            base_url=model_config["base_url"],
            api_key=self._get_api_key(model_config["provider"]),
        )
        try:
            extra_body = self._build_extra_body(
                provider=model_config["provider"],
                enable_thinking=enable_thinking,
                stream=True,
            )
            logger.info(
                "llm.global request: provider=%s model=%s selected=%s",
                model_config["provider"],
                model_config["model"],
                selected_model,
            )
            self.last_debug_info = {
                "stage": "global_answer",
                "status": "requesting",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "extra_body": extra_body,
                "thinking_effective": bool(extra_body and extra_body.get("enable_thinking")),
            }
            content, reasoning = self._stream_completion(
                client=client,
                model=model_config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个论文陪读智能体。",
                    },
                    {
                        "role": "user",
                        "content": build_global_agent_answer_prompt_with_context(
                            question=question,
                            conversation_context=conversation_context,
                            user_memory=user_memory,
                        ),
                    },
                ],
                extra_body=extra_body,
            )
            logger.info(
                "llm.global success: provider=%s model=%s has_content=%s has_reasoning=%s",
                model_config["provider"],
                model_config["model"],
                bool(content),
                bool(reasoning),
            )
            self.last_debug_info = {
                "stage": "global_answer",
                "status": "success",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "has_content": bool(content),
                "has_reasoning": bool(reasoning),
                "streaming_used": True,
            }
            return content
        except Exception as exc:
            self.last_debug_info = {
                "stage": "global_answer",
                "status": "failed",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "selected_model": selected_model,
                "base_url": model_config["base_url"],
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            logger.exception(
                "llm.global failed: provider=%s model=%s error=%s",
                model_config["provider"],
                model_config["model"],
                exc,
            )
            return None

    def generate_structured_analysis(
        self,
        title: str,
        abstract: str,
        sections: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        self.last_debug_info = None
        model_config = self.get_model_config(None)
        if model_config is None:
            self.last_debug_info = {
                "stage": "analysis",
                "status": "skipped",
                "reason": "no_enabled_external_model",
            }
            logger.info("llm.analysis skipped: no enabled external model, using heuristic overview")
            return None

        try:
            from openai import OpenAI
        except ImportError:
            self.last_debug_info = {
                "stage": "analysis",
                "status": "skipped",
                "reason": "openai_package_not_installed",
                "provider": model_config["provider"],
                "model": model_config["model"],
            }
            logger.warning("llm.analysis skipped: openai package not installed")
            return None

        client = OpenAI(
            base_url=model_config["base_url"],
            api_key=self._get_api_key(model_config["provider"]),
        )
        try:
            extra_body = self._build_extra_body(
                provider=model_config["provider"],
                enable_thinking=None,
                stream=True,
            )
            logger.info(
                "llm.analysis request: provider=%s model=%s title=%s",
                model_config["provider"],
                model_config["model"],
                title[:80],
            )
            self.last_debug_info = {
                "stage": "analysis",
                "status": "requesting",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "base_url": model_config["base_url"],
                "extra_body": extra_body,
                "thinking_effective": bool(extra_body and extra_body.get("enable_thinking")),
            }
            content = self._request_analysis_with_json_mode(
                client=client,
                model_config=model_config,
                title=title,
                abstract=abstract,
                sections=sections,
                chunks=chunks,
                extra_body=extra_body,
            )
            logger.info(
                "llm.analysis success: provider=%s model=%s has_content=%s",
                model_config["provider"],
                model_config["model"],
                bool(content),
            )
            self.last_debug_info = {
                "stage": "analysis",
                "status": "success",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "base_url": model_config["base_url"],
                "has_content": bool(content),
            }
        except Exception as exc:
            self.last_debug_info = {
                "stage": "analysis",
                "status": "failed",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "base_url": model_config["base_url"],
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            logger.exception(
                "llm.analysis failed: provider=%s model=%s error=%s",
                model_config["provider"],
                model_config["model"],
                exc,
            )
            return None
        if not content:
            return None
        return self._safe_load_json(content)

    def _get_api_key(self, provider: str) -> str:
        if provider == "modelscope":
            return settings.modelscope_api_key
        if provider == "dashscope":
            return settings.dashscope_api_key
        return ""

    def _build_extra_body(
        self,
        provider: str,
        enable_thinking: bool | None,
        stream: bool,
    ) -> dict[str, Any] | None:
        if provider == "modelscope":
            effective_enable = (
                settings.modelscope_enable_thinking if enable_thinking is None else enable_thinking
            )
            if not effective_enable:
                return None
            if not stream:
                self.last_debug_info = {
                    **(self.last_debug_info or {}),
                    "thinking_requested": True,
                    "thinking_effective": False,
                    "thinking_note": "enable_thinking is ignored for non-streaming calls",
                }
                return None
            payload: dict[str, Any] = {"enable_thinking": True}
            if settings.modelscope_thinking_budget:
                payload["thinking_budget"] = settings.modelscope_thinking_budget
            return payload
        if provider == "dashscope":
            effective_enable = (
                settings.dashscope_enable_thinking if enable_thinking is None else enable_thinking
            )
            if not effective_enable:
                return None
            if not stream:
                self.last_debug_info = {
                    **(self.last_debug_info or {}),
                    "thinking_requested": True,
                    "thinking_effective": False,
                    "thinking_note": "enable_thinking is ignored for non-streaming calls",
                }
                return None
            payload = {"enable_thinking": True}
            if settings.dashscope_thinking_budget:
                payload["thinking_budget"] = settings.dashscope_thinking_budget
            return payload
        return None

    def _request_analysis_with_json_mode(
        self,
        client: Any,
        model_config: dict[str, Any],
        title: str,
        abstract: str,
        sections: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
        extra_body: dict[str, Any] | None,
    ) -> str | None:
        messages = [
            {"role": "system", "content": "你是一个严谨的论文分析智能体。"},
            {
                "role": "user",
                "content": build_paper_analysis_prompt(
                    title=title,
                    abstract=abstract,
                    sections=sections,
                    chunks=chunks,
                ),
            },
        ]
        try:
            content, _ = self._stream_completion(
                client=client,
                model=model_config["model"],
                messages=messages,
                extra_body=extra_body,
                response_format={"type": "json_object"},
            )
            return content
        except Exception as exc:
            self.last_debug_info = {
                "stage": "analysis",
                "status": "retrying_without_json_mode",
                "provider": model_config["provider"],
                "model": model_config["model"],
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            logger.warning(
                "llm.analysis json_mode_retry: provider=%s model=%s error=%s",
                model_config["provider"],
                model_config["model"],
                exc,
            )
            content, _ = self._stream_completion(
                client=client,
                model=model_config["model"],
                messages=messages,
                extra_body=extra_body,
            )
            return content

    def _stream_completion(
        self,
        client: Any,
        model: str,
        messages: list[dict[str, str]],
        extra_body: dict[str, Any] | None,
        response_format: dict[str, Any] | None = None,
    ) -> tuple[str | None, str | None]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if extra_body:
            kwargs["extra_body"] = extra_body
        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        answer_parts: list[str] = []
        reasoning_parts: list[str] = []
        for chunk in response:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            reasoning_piece = getattr(delta, "reasoning_content", None)
            answer_piece = getattr(delta, "content", None)
            if reasoning_piece:
                reasoning_parts.append(reasoning_piece)
            if answer_piece:
                answer_parts.append(answer_piece)
        answer = "".join(answer_parts).strip() or None
        reasoning = "".join(reasoning_parts).strip() or None
        return answer, reasoning

    @staticmethod
    def _build_model_id(provider: str, model: str) -> str:
        sanitized = model.lower().replace("/", ":").replace(" ", "-")
        return f"{provider}:{sanitized}"

    @staticmethod
    def _safe_load_json(content: str) -> dict[str, Any] | None:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None
