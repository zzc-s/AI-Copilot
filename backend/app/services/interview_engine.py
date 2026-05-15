from __future__ import annotations

import hashlib
import uuid
from statistics import mean
from typing import Any

from app.services.question_bank import BUCKETS, buckets_for_keywords
from app.services.interview_llm_generator import generate_interview_questions_by_llm, should_use_llm


def build_questions(
    role: str,
    *,
    jd_id: uuid.UUID | None = None,
    jd_parsed: dict[str, Any] | None = None,
    jd_snippets: list[str] | None = None,
    company: str = "",
    jd_raw_text: str = "",
) -> list[dict[str, Any]]:
    """
    根据岗位、JD 解析结果生成面试题。
    
    策略：
    1. 优先使用 LLM 根据 JD 动态生成个性化题目
    2. 如果 LLM 不可用或失败，回退到固定题库
    
    同 jd_id 结果稳定（基于哈希确定性）。
    """
    jd_parsed = jd_parsed or {}
    
    # 第一步：尝试使用 LLM 生成
    if should_use_llm() and company:
        llm_questions = generate_interview_questions_by_llm(
            role=role,
            company=company,
            jd_parsed=jd_parsed,
            jd_raw_text=jd_raw_text,
        )
        if llm_questions and len(llm_questions) >= 5:
            return llm_questions[:5]
    
    # 第二步：回退到固定题库（原有逻辑）
    return _build_questions_from_bank(
        role=role,
        jd_id=jd_id,
        jd_parsed=jd_parsed,
    )


def _build_questions_from_bank(
    role: str,
    *,
    jd_id: uuid.UUID | None = None,
    jd_parsed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    从固定题库中选题（作为 LLM 生成失败的回退方案）。
    """
    jd_parsed = jd_parsed or {}
    keywords: list[str] = list(jd_parsed.get("keywords") or [])
    bucket_ids = buckets_for_keywords(keywords)
    if "generic" not in bucket_ids:
        bucket_ids.append("generic")

    seed = hashlib.sha256(f"{jd_id or 'no-id'}|{role}".encode("utf-8")).digest()

    def idx(off: int, n: int) -> int:
        if n <= 0:
            return 0
        return int.from_bytes(seed[off % 28 : off % 28 + 4], "big") % n

    pools: list[list[dict[str, Any]]] = [BUCKETS[bid] for bid in bucket_ids if bid in BUCKETS]

    out: list[dict[str, Any]] = []
    used_texts: set[str] = set()  # 用于去重

    def pick_unique(pool: list[dict[str, Any]], off: int, max_attempts: int = 10) -> dict[str, Any] | None:
        """从池中选取一道不重复的题目"""
        for attempt in range(max_attempts):
            i = idx(off + attempt * 7, len(pool))  # 每次尝试用不同的偏移
            q = pool[i]
            text = q.get("question_text", "")
            if text and text not in used_texts:
                used_texts.add(text)
                return dict(q)
        # 如果都重复了，返回 None
        return None

    # 1：主分桶第一题
    p0 = pools[0]
    t0 = pick_unique(p0, 0)
    if t0:
        out.append(t0)

    # 2：主分桶或第二分桶
    p_sel = pools[1] if len(pools) > 1 else p0
    t1 = pick_unique(p_sel, 4)
    if t1:
        out.append(t1)

    # 3：从所有可用分桶轮询选取（避免只从 generic 选）
    for pool_idx, offset in [(0, 8), (1, 12), (0, 16)]:
        if len(out) >= 5:
            break
        if pool_idx < len(pools):
            q = pick_unique(pools[pool_idx], offset)
            if q:
                out.append(q)

    # 4：如果还不够5题，从 generic 补充
    g = BUCKETS["generic"]
    offset = 20
    while len(out) < 5:
        q = pick_unique(g, offset)
        if q:
            out.append(q)
        offset += 7
        if offset > 100:  # 防止无限循环
            break

    return out[:5]


def evaluate_answer(answer_text: str) -> tuple[float, dict]:
    length_score = min(len(answer_text) / 120, 1.0) * 40
    structure_bonus = 20 if "首先" in answer_text or "第一" in answer_text else 0
    result_bonus = 20 if "%" in answer_text or "提升" in answer_text or "降低" in answer_text else 10
    score = round(min(length_score + structure_bonus + result_bonus + 20, 100), 2)
    feedback = {
        "strengths": ["回答完整度较好"] if score > 70 else ["有基本回答思路"],
        "improvements": ["增加量化结果", "使用 STAR 结构描述"] if score < 85 else ["可进一步压缩表述并突出影响"],
    }
    return score, feedback


def summarize_session(scores: list[float]) -> tuple[float, str]:
    if not scores:
        return 0.0, "尚未作答"
    overall = round(mean(scores), 2)
    if overall >= 85:
        summary = "整体表现优秀，可重点优化表达精炼度。"
    elif overall >= 70:
        summary = "表现良好，建议增强量化成果和问题拆解能力。"
    else:
        summary = "基础尚可，需强化项目深度与结构化表达。"
    return overall, summary
