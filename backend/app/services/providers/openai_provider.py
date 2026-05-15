from __future__ import annotations

import time
from typing import Any

from openai import OpenAI

from app.services.providers.base import ASRProvider, EmbeddingProvider, LLMProvider


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, base_url: str | None) -> None:
        # 使用 httpx 客户端避免 proxies 参数错误
        import httpx
        http_client = httpx.Client(timeout=60.0)
        self._client = OpenAI(api_key=api_key, base_url=base_url or None, http_client=http_client)

    def chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        start = time.perf_counter()
        resp = self._client.chat.completions.create(model=model, messages=messages)
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        usage = resp.usage
        return {
            "text": text,
            "model_name": model,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "latency_ms": latency_ms,
        }


class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, api_key: str, base_url: str | None) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=120.0)

    def embed(self, texts: list[str], model: str) -> dict[str, Any]:
        start = time.perf_counter()
        resp = self._client.embeddings.create(model=model, input=texts)
        latency_ms = int((time.perf_counter() - start) * 1000)
        data = sorted(resp.data, key=lambda x: x.index)
        vectors = [list(d.embedding) for d in data]
        usage = resp.usage
        return {
            "vectors": vectors,
            "model_name": model,
            "input_tokens": usage.prompt_tokens if usage else sum(len(t) // 4 for t in texts),
            "latency_ms": latency_ms,
        }


class OpenAIWhisperASR(ASRProvider):
    def __init__(self, api_key: str, base_url: str | None) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url or None, timeout=120.0)

    def transcribe(self, audio_bytes: bytes, mime_type: str, model: str) -> dict[str, Any]:
        start = time.perf_counter()
        import io

        buf = io.BytesIO(audio_bytes)
        buf.name = "audio.webm" if "webm" in mime_type else "audio.wav"
        resp = self._client.audio.transcriptions.create(model=model, file=buf)
        latency_ms = int((time.perf_counter() - start) * 1000)
        text = getattr(resp, "text", None) or str(resp)
        return {
            "text": text.strip(),
            "model_name": model,
            "input_tokens": len(audio_bytes) // 50,
            "latency_ms": latency_ms,
        }
