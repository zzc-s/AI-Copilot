"""
面试题固定题库 - 已弃用

注意：本文件保留作为 LLM 生成失败时的应急回退方案。
实际项目应优先使用 interview_llm_generator 根据 JD 动态生成题目。

如需完全移除固定题库，可将 build_questions 中的回退逻辑删除。
"""

from __future__ import annotations

from typing import Any

# 空题库，保留结构但不提供实际题目
BUCKETS: dict[str, list[dict[str, Any]]] = {
    "generic": [
        {
            "question_text": "请用 STAR 法则描述一次你解决复杂问题的经历。",
            "dimension": "behavior",
            "difficulty": "medium",
        },
    ],
}


def buckets_for_keywords(keywords: list[str]) -> list[str]:
    """始终返回通用桶，不再根据关键词匹配。"""
    return ["generic"]
