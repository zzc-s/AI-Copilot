"""使用 LLM 根据 JD 和简历生成个性化改写建议。"""

from __future__ import annotations

import json
from typing import Any

from app.services.providers import get_llm_provider
from app.core.config import settings


def should_use_llm() -> bool:
    """判断是否可以使用真实 LLM。"""
    if settings.llm_provider == "mock" or not settings.llm_api_key:
        return False
    try:
        provider = get_llm_provider()
        from app.services.providers.mock_provider import MockLLM
        if isinstance(provider, MockLLM):
            return False
        return True
    except Exception:
        return False


def build_prompt_for_resume_advice(
    jd_company: str,
    jd_role: str,
    jd_parsed: dict[str, Any],
    resume_text: str,
    matched_keywords: list[str],
    missing_keywords: list[str],
) -> list[dict[str, str]]:
    """构建 Prompt 请求 LLM 生成改写建议。"""
    
    keywords_str = ", ".join(missing_keywords[:8]) if missing_keywords else "无"
    hit_keywords_str = ", ".join(matched_keywords[:5]) if matched_keywords else "无"
    
    system_content = """你是求职 AI Copilot 的简历优化专家。

请根据 JD（职位描述）和候选人的简历，提供 3-5 条具体、可执行的改写建议。

建议要求：
1. 针对性强：每条建议对应一个 JD 要求，指出具体哪里需要改
2. 可执行：给出明确的改写方向或示例思路
3. 分类清晰：区分项目经历、技能栏、个人总结三个维度
4. 简洁：每条建议 1-2 句话，不要冗长

输出格式（必须是合法 JSON）：
{
  "project_experience": ["建议1", "建议2", ...],
  "skills": ["建议1", "建议2", ...],
  "profile": ["建议1", ...]
}

注意：
- 只输出 JSON，不要 Markdown 围栏
- 建议要具体，避免泛泛而谈"优化简历"之类的话
- 针对缺失的技能关键词给出补充建议"""

    user_content = f"""【JD 公司】{jd_company}
【JD 岗位】{jd_role}
【JD 关键词】{keywords_str}
【简历已覆盖】{hit_keywords_str}

【JD 详细描述】
{jd_parsed.get('raw_text', '')[:600]}

【候选人简历】
{resume_text[:800]}

请分析简历与 JD 的匹配度，提供具体改写建议（JSON 格式）："""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_resume_advice_by_llm(
    jd_company: str,
    jd_role: str,
    jd_parsed: dict[str, Any],
    resume_text: str,
    matched_keywords: list[str],
    missing_keywords: list[str],
) -> dict[str, list[str]] | None:
    """
    调用 LLM 生成个性化简历改写建议。
    
    Returns:
        包含 project_experience, skills, profile 三个列表的字典
        如果失败返回 None，让调用方使用模板方案
    """
    try:
        messages = build_prompt_for_resume_advice(
            jd_company, jd_role, jd_parsed, resume_text,
            matched_keywords, missing_keywords
        )
        
        provider = get_llm_provider()
        model = settings.llm_model_primary or "gpt-4o-mini"
        
        out = provider.chat(messages, model)
        result_text = out.get("text", "").strip()
        
        if not result_text:
            return None
        
        # 清理 Markdown 围栏
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # 解析 JSON
        try:
            advice = json.loads(result_text)
            if isinstance(advice, dict):
                return {
                    "project_experience": advice.get("project_experience", [])[:6],
                    "skills": advice.get("skills", [])[:4],
                    "profile": advice.get("profile", [])[:3],
                }
        except json.JSONDecodeError as e:
            print(f"LLM 返回结果解析失败: {e}")
            print(f"返回内容: {result_text[:200]}...")
            
        return None
        
    except Exception as e:
        print(f"LLM 生成简历建议失败: {e}")
        return None
