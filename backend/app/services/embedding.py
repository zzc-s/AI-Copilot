"""文本向量：调用 EmbeddingProvider。"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.services.providers import get_embedding_provider

logger = logging.getLogger(__name__)


def embed_texts(texts: list[str]) -> tuple[list[list[float]], dict[str, Any]]:
    """返回 (vectors, meta)。"""
    if not texts:
        return [], {}
    prov = get_embedding_provider()
    model = settings.embedding_model
    try:
        out = prov.embed(texts, model)
        vecs = out.get("vectors") or []
        meta = {
            "model_name": out.get("model_name"),
            "input_tokens": out.get("input_tokens", 0),
            "latency_ms": out.get("latency_ms", 0),
        }
        return vecs, meta
    except Exception as exc:
        logger.exception("embed_texts failed: %s", exc)
        raise


def cosine_score_unit_vectors(a: list[float], b: list[float]) -> float:
    """余弦相似度映射到 0–100（假定已单位化）。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    # 单位向量 dot ∈ [-1, 1]
    return round(((dot + 1.0) / 2.0) * 100, 2)


def split_jd_chunks(raw_text: str, max_chunk: int = 600) -> list[str]:
    parts = [p.strip() for p in raw_text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    if not parts:
        return [raw_text.strip()[:max_chunk]] if raw_text.strip() else []
    chunks: list[str] = []
    for p in parts:
        if len(p) <= max_chunk:
            chunks.append(p)
        else:
            for i in range(0, len(p), max_chunk):
                chunks.append(p[i : i + max_chunk])
    return chunks[:24]
