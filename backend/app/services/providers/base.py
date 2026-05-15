from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        """Return dict with keys: text, model_name, input_tokens, output_tokens, latency_ms."""


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str], model: str) -> dict[str, Any]:
        """Return dict with keys: vectors (list[list[float]]), model_name, input_tokens, latency_ms."""


class ASRProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime_type: str, model: str) -> dict[str, Any]:
        """Return dict with keys: text, model_name, input_tokens, latency_ms."""
