"""在已配置真实 LLM 时增强规则引擎输出；失败或未配置时静默回退。"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.services.providers import get_llm_provider

_log = logging.getLogger(__name__)


def should_augment() -> bool:
    if not getattr(settings, "llm_augment", True):
        return False
    if settings.llm_provider.lower() == "mock":
        return False
    if not (settings.llm_api_key or "").strip():
        return False
    return True


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(_strip_code_fence(text))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _parse_json_arr(text: str) -> list[Any] | None:
    try:
        obj = json.loads(_strip_code_fence(text))
        return obj if isinstance(obj, list) else None
    except json.JSONDecodeError:
        return None


def augment_parsed_jd(fallback: dict[str, Any], *, role: str, company: str, raw_text: str) -> dict[str, Any]:
    if not should_augment():
        return fallback
    try:
        prov = get_llm_provider()
        excerpt = raw_text[:4000]
        instruction = (
            f"岗位名称：{role}\n公司：{company}\n\n请阅读下列职位描述，输出一个 JSON 对象，键为："
            "responsibilities, requirements, keywords；均为中文字符串数组。"
            f"\n\n职位描述：\n{excerpt}"
        )
        out = prov.chat(
            [
                {"role": "system", "content": "只输出一个 JSON 对象，不要 Markdown 围栏或其他说明。"},
                {"role": "user", "content": instruction},
            ],
            settings.llm_model_primary,
        )
        parsed = _parse_json_obj(out.get("text") or "")
        if not parsed:
            return fallback
        merged = dict(fallback)
        for key in ("responsibilities", "requirements", "keywords"):
            v = parsed.get(key)
            if isinstance(v, list) and all(isinstance(x, str) for x in v) and v:
                merged[key] = v
        merged["role"] = role
        return merged
    except Exception as exc:
        _log.debug("augment_parsed_jd failed: %s", exc)
        return fallback


def augment_rewrite_suggestions(
    fallback: dict[str, Any],
    *,
    jd_parsed: dict[str, Any],
    resume_text: str,
) -> dict[str, Any]:
    if not should_augment():
        return fallback
    try:
        prov = get_llm_provider()
        instruction = (
            "根据下列 JD 摘要与简历全文，输出 JSON，键：project_experience, skills, profile；"
            "值均为中文字符串数组（每条建议一行，具体可执行）。\n\n"
            f"JD 摘要：{json.dumps({k: jd_parsed.get(k) for k in ('keywords', 'responsibilities')}, ensure_ascii=False)[:2500]}\n\n"
            f"简历：\n{resume_text[:4500]}\n\n"
            f"规则草案（可改写覆盖）：\n{json.dumps(fallback, ensure_ascii=False)[:3500]}"
        )
        out = prov.chat(
            [
                {"role": "system", "content": "只输出 JSON 对象。"},
                {"role": "user", "content": instruction},
            ],
            settings.llm_model_primary,
        )
        parsed = _parse_json_obj(out.get("text") or "")
        if not parsed:
            return fallback
        merged = dict(fallback)
        for key in ("project_experience", "skills", "profile"):
            v = parsed.get(key)
            if isinstance(v, list) and all(isinstance(x, str) for x in v) and v:
                merged[key] = v
        return merged
    except Exception as exc:
        _log.debug("augment_rewrite_suggestions failed: %s", exc)
        return fallback


def augment_interview_questions(
    questions: list[dict[str, Any]],
    *,
    role: str,
    jd_excerpt: str,
) -> list[dict[str, Any]]:
    if not should_augment() or not questions:
        return questions
    try:
        prov = get_llm_provider()
        draft = json.dumps(questions, ensure_ascii=False)
        instruction = (
            f"岗位：{role}\nJD 摘录：{jd_excerpt[:2000]}\n\n"
            "下列面试题 JSON 数组请改写 question_text 使其更贴近 JD，保留 dimension、difficulty 不变。"
            f"\n{draft}"
        )
        out = prov.chat(
            [
                {"role": "system", "content": "只输出 JSON 数组，元素含 question_text, dimension, difficulty。"},
                {"role": "user", "content": instruction},
            ],
            settings.llm_model_primary,
        )
        arr = _parse_json_arr(out.get("text") or "")
        if not arr or len(arr) != len(questions):
            return questions
        merged = []
        for i, q in enumerate(questions):
            item = arr[i] if i < len(arr) else {}
            if isinstance(item, dict) and isinstance(item.get("question_text"), str):
                nq = dict(q)
                nq["question_text"] = item["question_text"]
                merged.append(nq)
            else:
                merged.append(q)
        return merged
    except Exception as exc:
        _log.debug("augment_interview_questions failed: %s", exc)
        return questions


def augment_plan(fallback: dict[str, Any], *, context: str) -> dict[str, Any]:
    if not should_augment():
        return fallback
    try:
        prov = get_llm_provider()
        instruction = (
            "下列为 7 日训练计划 JSON。请只改写 daily_tasks 中每项的 task 字段，使其更具体、可执行，"
            "可引用上下文中的关键词；保留 level、session_id 及其他结构不变。\n\n"
            f"上下文：{context[:2000]}\n\n计划：\n{json.dumps(fallback, ensure_ascii=False)[:6000]}"
        )
        out = prov.chat(
            [
                {"role": "system", "content": "只输出一个 JSON 对象，结构与输入一致。"},
                {"role": "user", "content": instruction},
            ],
            settings.llm_model_primary,
        )
        parsed = _parse_json_obj(out.get("text") or "")
        if not parsed or "daily_tasks" not in parsed:
            return fallback
        new_tasks = parsed.get("daily_tasks")
        old_tasks = fallback.get("daily_tasks") or []
        if not isinstance(new_tasks, list) or len(new_tasks) != len(old_tasks):
            return fallback
        merged = dict(fallback)
        daily = []
        for i, old in enumerate(old_tasks):
            nt = new_tasks[i] if i < len(new_tasks) else {}
            cell = dict(old)
            if isinstance(nt, dict) and isinstance(nt.get("task"), str):
                cell["task"] = nt["task"]
            daily.append(cell)
        merged["daily_tasks"] = daily
        return merged
    except Exception as exc:
        _log.debug("augment_plan failed: %s", exc)
        return fallback
