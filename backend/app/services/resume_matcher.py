from __future__ import annotations

import re
from typing import Any

from app.services.resume_llm_advisor import (
    generate_resume_advice_by_llm,
    should_use_llm as should_use_llm_for_advice,
)


def structure_resume(raw_text: str) -> dict:
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    return {"sections": paragraphs}


def _split_resume_sections(resume_text: str) -> dict[str, list[str]]:
    paras = [p.strip() for p in resume_text.split("\n\n") if p.strip()]
    hints: dict[str, list[str]] = {"project": [], "skills": [], "education": [], "other": []}
    proj_kw = ("项目", "实习", "业绩", "负责", "重构", "优化", "设计")
    skill_kw = ("技能", "技术栈", "熟悉", "掌握", "了解", "工具")
    edu_kw = ("教育", "大学", "专业", "GPA", "主修", "学院")
    for p in paras:
        if any(k in p for k in proj_kw):
            hints["project"].append(p[:220])
        elif any(k in p for k in skill_kw):
            hints["skills"].append(p[:220])
        elif any(k in p for k in edu_kw):
            hints["education"].append(p[:220])
        else:
            hints["other"].append(p[:220])
    return hints


def _evidence_for_keyword(keyword: str, evidence: list[str] | None) -> str | None:
    if not evidence:
        return None
    kl = keyword.lower()
    for e in evidence:
        if kl in e.lower():
            return e[:420].replace("\n", " ")
    return evidence[0][:420].replace("\n", " ")


def _suggest_target_section(keyword: str) -> str:
    k = keyword.lower()
    if any(x in k for x in ("sql", "mysql", "redis", "kafka", "java", "python", "go", "spring")):
        return "项目经历"
    if "沟通" in keyword or "协作" in keyword:
        return "个人总结 / 自我评价"
    return "项目经历或技能栏"


def _build_fallback_advice(miss: list[str]) -> dict[str, list[str]]:
    """模板化的改写建议（LLM 失败时的回退方案）。"""
    project_lines = []
    skills_lines = []
    
    for m in miss[:6]:
        tgt = _suggest_target_section(m)
        project_lines.append(
            f"建议在「{tgt}」补充与「{m}」相关的项目案例，包含具体场景、性能指标（如延迟/QPS/命中率）和业务成果。"
        )
    
    for m in miss[:4]:
        skills_lines.append(f"技能栏增加「{m}」（熟练度 + 生产案例一行），避免只列名词。")
    
    return {
        "project_experience": project_lines or ["在项目经历中补充与 JD 职责段落对应的案例与指标"],
        "skills": skills_lines,
        "profile": ["个人总结中用 2–3 条 bullet，把命中关键词与业务成果绑定（数字 + 对比）。"],
    }


def match_resume_to_jd(
    resume_text: str,
    jd_parsed: dict,
    *,
    jd_company: str = "",
    jd_role: str = "",
    vector_score: float | None = None,
    jd_evidence: list[str] | None = None,
) -> tuple[float, dict, dict]:
    resume_lower = resume_text.lower()
    jd_keywords: list[str] = list(jd_parsed.get("keywords") or [])

    if not jd_keywords:
        keyword_score = 65.0
        gap: dict[str, Any] = {"missing_keywords": [], "matched_keywords": []}
        rewrite: dict[str, Any] = {
            "summary": ["补充和岗位更相关的项目描述，并与 JD 中的职责条目逐条对齐"],
            "project_experience": [],
            "skills": [],
            "profile": [],
        }
        final_score = keyword_score
        if vector_score is not None:
            final_score = round(0.5 * keyword_score + 0.5 * vector_score, 2)
            gap["vector_score"] = vector_score
        return final_score, gap, rewrite

    hit = [k for k in jd_keywords if k.lower() in resume_lower]
    miss = [k for k in jd_keywords if k.lower() not in resume_lower]
    keyword_score = round(60 + (len(hit) / len(jd_keywords)) * 40, 2)
    gap = {"matched_keywords": hit, "missing_keywords": miss}
    if vector_score is not None:
        gap["vector_score"] = vector_score

    # 尝试使用 LLM 生成个性化改写建议
    rewrite: dict[str, Any]
    if should_use_llm_for_advice() and jd_company and resume_text:
        llm_advice = generate_resume_advice_by_llm(
            jd_company=jd_company,
            jd_role=jd_role,
            jd_parsed=jd_parsed,
            resume_text=resume_text,
            matched_keywords=hit,
            missing_keywords=miss,
        )
        if llm_advice:
            rewrite = {
                "project_experience": llm_advice.get("project_experience", []),
                "skills": llm_advice.get("skills", []),
                "profile": llm_advice.get("profile", []),
                "source": "llm",  # 标记来自 LLM
            }
        else:
            # LLM 失败，使用模板
            rewrite = _build_fallback_advice(miss)
            rewrite["source"] = "fallback"
    else:
        # 无 LLM 配置，使用模板
        rewrite = _build_fallback_advice(miss)
        rewrite["source"] = "fallback"

    if vector_score is None:
        return keyword_score, gap, rewrite
    final_score = round(0.5 * keyword_score + 0.5 * vector_score, 2)
    return final_score, gap, rewrite
