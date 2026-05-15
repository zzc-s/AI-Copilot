from __future__ import annotations

from app.core.config import settings
from app.services.providers.aliyun_asr_provider import AliyunASR
from app.services.providers.base import ASRProvider, EmbeddingProvider, LLMProvider
from app.services.providers.mock_provider import MockASR, MockEmbedding, MockLLM
from app.services.providers.openai_provider import OpenAIEmbedding, OpenAILLM, OpenAIWhisperASR


def get_llm_provider() -> LLMProvider:
    p = settings.llm_provider.lower()
    if p == "mock":
        return MockLLM()
    if p in ("openai", "compatible"):
        if not settings.llm_api_key:
            return MockLLM()
        return OpenAILLM(api_key=settings.llm_api_key, base_url=settings.llm_base_url or None)
    return MockLLM()


def get_embedding_provider() -> EmbeddingProvider:
    p = settings.embedding_provider.lower()
    if p == "mock":
        return MockEmbedding(settings.embedding_dim)
    if p in ("openai", "compatible"):
        if not settings.llm_api_key:
            return MockEmbedding(settings.embedding_dim)
        return OpenAIEmbedding(api_key=settings.llm_api_key, base_url=settings.llm_base_url or None)
    return MockEmbedding(settings.embedding_dim)


def get_asr_provider() -> ASRProvider:
    p = settings.asr_provider.lower()
    if p == "mock":
        return MockASR()
    if p == "aliyun":
        # 解析 ASR_API_KEY 格式: "access_key_id:access_key_secret"
        api_key = settings.asr_api_key or ""
        if ":" in api_key:
            parts = api_key.split(":", 1)
            access_key_id = parts[0]
            access_key_secret = parts[1]
            app_key = settings.asr_app_key or ""
            if access_key_id and access_key_secret and app_key:
                return AliyunASR(
                    access_key_id=access_key_id,
                    access_key_secret=access_key_secret,
                    app_key=app_key,
                    ffmpeg_executable=(settings.ffmpeg_path or "").strip() or None,
                )
        # 配置不完整，回退到 Mock
        print("Aliyun ASR config incomplete, fallback to MockASR")
        return MockASR()
    if p in ("openai_whisper", "compatible", "openai"):
        if not settings.llm_api_key:
            return MockASR()
        return OpenAIWhisperASR(api_key=settings.llm_api_key, base_url=settings.llm_base_url or None)
    return MockASR()


__all__ = [
    "get_llm_provider",
    "get_embedding_provider",
    "get_asr_provider",
    "LLMProvider",
    "EmbeddingProvider",
    "ASRProvider",
]
