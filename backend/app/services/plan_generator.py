"""根据得分与薄弱维度生成差异化 7 日训练计划（规则引擎；可选 LLM 覆盖）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _fmt_kw(missing: list[str], i: int) -> str:
    if not missing:
        return "岗位相关基础"
    return "、".join(missing[: min(3, len(missing))])


def _day_templates(
    level: str,
    missing_keywords: list[str],
    weak_dimensions: list[str],
) -> list[str]:
    """7 天主题固定轮换，但内容会嵌入 missing_keywords / weak_dimensions。"""
    weak_txt = "、".join(weak_dimensions[:3]) if weak_dimensions else "综合表达与项目深度"
    mk = _fmt_kw(missing_keywords, 0)

    if level == "advanced":
        return [
            f"模拟 1 次技术方案评审：针对「{mk}」设计接口与数据流，并写出风险清单。",
            f"完成 1 道中等难度系统设计题，主题与「{mk}」或当前岗位栈相关。",
            f"复盘一个生产事故 / 慢查询，用 STAR 写满一页，并补充监控与预案。",
            f"针对薄弱维度「{weak_txt}」各写 1 个行为题回答（每题 200 字+量化结果）。",
            f"与「{mk}」相关的源码 / 官方文档精读 1 章，并整理 5 条可落地笔记。",
            f"全栈或上下游联调：画出一条请求链路时序图，标出缓存 / MQ / DB 边界。",
            f"简历增量迭代：把本周产出合并进项目描述，突出与 JD 关键词「{mk}」的匹配。",
        ]

    return [
        f"STAR 专项：选 2 段经历，分别补齐情境-任务-行动-结果，并量化指标（关联「{mk}」）。",
        f"八股 + 实践：围绕「{mk}」各整理 5 个高频问答，并各附一行项目佐证。",
        f"项目深挖：选择负责最多的一块模块，写出输入输出、边界条件与失败兜底。",
        f"行为与协作：针对「{weak_txt}」写 2 个场景题答案并录音 5 分钟自评。",
        f"慢查询 / 性能：准备一页笔记：索引、Explain、连接池与批处理（结合「{mk}」）。",
        f"模拟面试：完整回答 3 题（1 基础 + 1 项目 + 1 行为），限时每题 4 分钟。",
        f"总结与计划：把本周笔记压缩成「一页纸」，列出下周待补强关键词（含「{mk}」）。",
    ]


def generate_plan(
    overall_score: float | None,
    *,
    missing_keywords: list[str] | None = None,
    weak_dimensions: list[str] | None = None,
    session_id: uuid.UUID | None = None,
) -> tuple[datetime, dict]:
    start_date = datetime.now(timezone.utc)
    level = "advanced" if (overall_score or 0) >= 80 else "foundation"
    mk = list(missing_keywords or [])
    wd = list(weak_dimensions or [])

    themes = _day_templates(level, mk, wd)

    daily_tasks = []
    for i in range(7):
        day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_tasks.append(
            {
                "day": day,
                "day_index": i + 1,
                "task": themes[i],
                "focus_keywords": mk[:5],
                "weak_dimensions": wd[:5],
                "done": False,
            }
        )

    plan = {
        "level": level,
        "session_id": str(session_id) if session_id else None,
        "daily_tasks": daily_tasks,
        "meta": {
            "missing_keywords_sample": mk[:8],
            "weak_dimensions": wd[:8],
        },
    }
    return start_date, plan
