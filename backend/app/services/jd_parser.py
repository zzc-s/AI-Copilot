"""JD 规则解析：分段职责 / 要求 + 关键词命中（不调用 LLM）。"""

from __future__ import annotations

import re
from typing import Iterable

# 常见小节标题（用于切分正文）
_RESP_HEADER = re.compile(
    r"^\s*(岗位职责|工作内容|工作职责|主要职责|职位描述|你将负责|工作描述)[:：]?\s*$",
    re.I,
)
_REQ_HEADER = re.compile(
    r"^\s*(任职要求|岗位要求|任职资格|必备条件|我们需要你|职位要求)[:：]?\s*$",
    re.I,
)

_KEYWORD_CANDIDATES: tuple[str, ...] = (
    "Java",
    "Python",
    "Go",
    "Golang",
    "C++",
    "Rust",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "MongoDB",
    "Elasticsearch",
    "Kafka",
    "RabbitMQ",
    "RocketMQ",
    "Spring",
    "Spring Boot",
    "MyBatis",
    "FastAPI",
    "Django",
    "Vue",
    "React",
    "TypeScript",
    "JavaScript",
    "微服务",
    "分布式",
    "Kubernetes",
    "K8s",
    "Docker",
    "Linux",
    "沟通协作",
    "沟通",
    "算法",
    "机器学习",
    "深度学习",
    "大模型",
    "LLM",
    "NLP",
    "广告",
    "推荐系统",
    "高并发",
)


def _normalize_line(line: str) -> str:
    return line.strip().strip("-•·").strip()


def _is_bullet(line: str) -> bool:
    s = line.strip()
    return bool(s) and (
        re.match(r"^[\d一二三四五六七八九十]+[\.、．]\s*", s)
        or s.startswith(("-", "•", "·", "*"))
        or len(s) > 8
    )


def _split_sections(lines: list[str]) -> tuple[list[str], list[str]]:
    mode: str | None = None
    resp: list[str] = []
    req: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if _RESP_HEADER.match(line):
            mode = "resp"
            continue
        if _REQ_HEADER.match(line):
            mode = "req"
            continue
        if not line.strip():
            continue
        norm = _normalize_line(line)
        if not norm:
            continue
        if mode == "resp":
            resp.append(norm)
        elif mode == "req":
            req.append(norm)
    return resp, req


def _fallback_chunks(lines: Iterable[str]) -> tuple[list[str], list[str]]:
    items = [_normalize_line(x) for x in lines if _normalize_line(x)]
    if not items:
        return [], []
    mid = max(1, len(items) // 2)
    return items[:mid], items[mid : mid + 8]


def _extract_keywords(raw_text: str) -> list[str]:
    lower = raw_text.lower()
    hits: list[tuple[int, str]] = []
    for kw in _KEYWORD_CANDIDATES:
        idx = lower.find(kw.lower())
        if idx >= 0:
            hits.append((idx, kw))
    hits.sort(key=lambda x: x[0])
    seen: set[str] = set()
    out: list[str] = []
    for _, kw in hits:
        if kw not in seen:
            seen.add(kw)
            out.append(kw)
    return out[:20]


def parse_jd(raw_text: str, role: str) -> dict:
    lines = raw_text.splitlines()
    resp_lines, req_lines = _split_sections(lines)

    if not resp_lines and not req_lines:
        stripped = [_normalize_line(x) for x in lines if _normalize_line(x)]
        resp_lines, req_lines = _fallback_chunks(stripped)

    responsibilities = resp_lines[:12] if resp_lines else []
    requirements = req_lines[:12] if req_lines else []

    if not responsibilities and not requirements:
        stripped = [_normalize_line(x) for x in lines if _normalize_line(x)]
        responsibilities = stripped[:8]
        requirements = stripped[8:16]

    keywords = _extract_keywords(raw_text)

    return {
        "role": role,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "keywords": keywords,
    }
