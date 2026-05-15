from __future__ import annotations

import hashlib
import math
import time
from typing import Any

from app.services.providers.base import ASRProvider, EmbeddingProvider, LLMProvider


def _hash_vec(text: str, dim: int) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    nums = []
    for i in range(dim):
        seed = (h[i % len(h)] + i * 31) % 256
        nums.append((seed / 127.5) - 1.0)
    norm = math.sqrt(sum(x * x for x in nums)) or 1.0
    return [x / norm for x in nums]


class MockLLM(LLMProvider):
    def chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        start = time.perf_counter()
        payload_echo = {"messages": messages}
        text = f"[mock:{model}] ok"
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "text": text,
            "model_name": model or "mock-llm",
            "input_tokens": 200,
            "output_tokens": 300,
            "latency_ms": latency_ms,
            "raw": payload_echo,
        }


class MockEmbedding(EmbeddingProvider):
    def __init__(self, dim: int) -> None:
        self.dim = dim

    def embed(self, texts: list[str], model: str) -> dict[str, Any]:
        start = time.perf_counter()
        vectors = [_hash_vec(t, self.dim) for t in texts]
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "vectors": vectors,
            "model_name": model or "mock-embedding",
            "input_tokens": sum(len(t) // 4 for t in texts),
            "latency_ms": latency_ms,
        }


class MockASR(ASRProvider):
    def transcribe(self, audio_bytes: bytes, mime_type: str, model: str) -> dict[str, Any]:
        start = time.perf_counter()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "text": "[mock] 用户回答示意",
            "model_name": model or "mock-whisper",
            "input_tokens": len(audio_bytes) // 100,
            "latency_ms": latency_ms,
        }
