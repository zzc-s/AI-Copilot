"""LLM 调用入口：多模型路由 + 熔断回退，兼容原 LLMClient.generate 返回结构。"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.services.providers import get_llm_provider
from app.services.providers.mock_provider import MockLLM

logger = logging.getLogger(__name__)


def _pack_response(scene: str, payload: dict[str, Any], out: dict[str, Any]) -> dict[str, Any]:
    return {
        "result": {"scene": scene, "text": out.get("text", ""), "payload_echo": payload},
        "input_tokens": int(out.get("input_tokens", 0)),
        "output_tokens": int(out.get("output_tokens", 0)),
        "latency_ms": int(out.get("latency_ms", 0)),
        "model_name": str(out.get("model_name") or "unknown"),
    }


class LLMRouter:
    """primary → fallback → MockLLM；熔断时跳过 primary。"""

    def __init__(self) -> None:
        self._error_ts: list[float] = []
        self._circuit_open_until: float = 0.0

    def _circuit_should_skip_primary(self) -> bool:
        now = time.time()
        if now < self._circuit_open_until:
            return True
        window_start = now - 30
        self._error_ts = [t for t in self._error_ts if t > window_start]
        return False

    def _record_error(self) -> None:
        now = time.time()
        self._error_ts.append(now)
        window_start = now - 30
        recent = [t for t in self._error_ts if t > window_start]
        self._error_ts = recent
        if len(recent) >= 5:
            self._circuit_open_until = now + 60
            logger.warning("LLM circuit opened for 60s after 5 errors in 30s")

    def generate(self, scene: str, payload: dict[str, Any]) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": "You are Job AI Copilot. Respond briefly in Chinese when generating user-visible text.",
            },
            {"role": "user", "content": f"scene={scene}\ndata={json.dumps(payload, ensure_ascii=False)}"},
        ]

        primary_model = settings.llm_model_primary or "gpt-4o-mini"
        fallback_model = (settings.llm_model_fallback or "").strip()

        last_exc: Exception | None = None

        if not self._circuit_should_skip_primary():
            try:
                prov = get_llm_provider()
                out = prov.chat(messages, primary_model)
                return _pack_response(scene, payload, out)
            except Exception as exc:
                last_exc = exc
                logger.warning("LLM primary failed (%s): %s", primary_model, exc)
                self._record_error()

        if fallback_model:
            try:
                prov = get_llm_provider()
                out = prov.chat(messages, fallback_model)
                return _pack_response(scene, payload, out)
            except Exception as exc:
                last_exc = exc
                logger.warning("LLM fallback failed (%s): %s", fallback_model, exc)
                self._record_error()

        try:
            mock = MockLLM()
            out = mock.chat(messages, "mock-llm")
            return _pack_response(scene, payload, out)
        except Exception as exc:
            raise RuntimeError("LLM request failed after retries") from (last_exc or exc)


LLMClient = LLMRouter
