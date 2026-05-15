"""使用 LLM 根据 JD 动态生成面试题。"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.services.providers import get_llm_provider
from app.core.config import settings


def should_use_llm() -> bool:
    """判断是否可以使用真实 LLM 生成题目。"""
    # 如果配置为 mock 或没有 API key，则返回 False
    if settings.llm_provider == "mock" or not settings.llm_api_key:
        return False
    # 尝试获取 provider，如果是 MockLLM 则返回 False
    try:
        provider = get_llm_provider()
        from app.services.providers.mock_provider import MockLLM
        if isinstance(provider, MockLLM):
            return False
        return True
    except Exception:
        # 如果 provider 初始化失败，返回 False 使用回退方案
        return False


def build_prompt_for_questions(
    company: str,
    role: str,
    jd_parsed: dict[str, Any],
    jd_raw_text: str,
) -> list[dict[str, str]]:
    """构建用于生成面试题的完整 Prompt。"""
    
    keywords = ", ".join(jd_parsed.get("keywords", []))
    responsibilities = ", ".join(jd_parsed.get("responsibilities", [])[:5])
    requirements = ", ".join(jd_parsed.get("requirements", [])[:5])
    
    system_content = """你是求职 AI Copilot 的面试题生成专家。

你的任务是根据职位描述（JD）生成 5 道针对性技术面试题。

题目要求：
1. 第一题（基础）：考察核心技能的基础理论知识（dimension: basic, difficulty: medium）
2. 第二题（进阶）：考察技能的深入理解和实际应用（dimension: basic, difficulty: hard）
3. 第三题（项目经验）：考察实际项目经历和工程能力（dimension: project, difficulty: medium）
4. 第四题（场景设计）：考察问题解决和方案设计能力（dimension: project, difficulty: hard）
5. 第五题（综合能力）：考察系统思维或软技能（dimension: basic 或 project, difficulty: medium 或 hard）

输出要求：
- 必须是合法 JSON 数组
- 不要 Markdown 围栏（```json）
- 只输出 JSON，不要有其他说明文字
- 题目要具体、有针对性，能区分候选人水平

示例格式：
[
  {
    "question_text": "具体问题内容",
    "dimension": "basic",
    "difficulty": "medium"
  }
]"""

    user_content = f"""请根据以下 JD 生成 5 道面试题：

【公司】{company}
【岗位】{role}
【技能关键词】{keywords}
【岗位职责】{responsibilities}
【任职要求】{requirements}
【JD原文节选】{jd_raw_text[:600] if jd_raw_text else ""}

请生成 5 道题目（JSON 格式）："""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_interview_questions_by_llm(
    role: str,
    company: str,
    jd_parsed: dict[str, Any],
    jd_raw_text: str = "",
) -> list[dict[str, Any]] | None:
    """
    根据 JD 解析结果调用 LLM 生成 5 道针对性面试题。
    
    Args:
        role: 岗位名称
        company: 公司名称
        jd_parsed: JD 解析结果（包含 keywords, responsibilities, requirements 等）
        jd_raw_text: 原始 JD 文本（用于补充上下文）
    
    Returns:
        5 道题目的列表，每道题包含 question_text, dimension, difficulty
        如果 LLM 调用失败，返回 None（让调用方回退到固定题库）
    """
    try:
        # 构建 Prompt
        messages = build_prompt_for_questions(company, role, jd_parsed, jd_raw_text)
        
        # 获取 LLM provider 并调用
        provider = get_llm_provider()
        model = settings.llm_model_primary or "gpt-4o-mini"
        
        out = provider.chat(messages, model)
        
        # 解析返回结果
        result_text = out.get("text", "").strip()
        if not result_text:
            return None
        
        # 清理可能的 Markdown 围栏
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
            
        # 尝试解析 JSON
        try:
            questions = json.loads(result_text)
            if isinstance(questions, list) and len(questions) >= 5:
                # 只取前5题，确保格式正确
                formatted_questions = []
                for i, q in enumerate(questions[:5]):
                    formatted_questions.append({
                        "id": str(uuid.uuid4()),
                        "question_text": q.get("question_text", q.get("question", "")),
                        "dimension": q.get("dimension", "basic"),
                        "difficulty": q.get("difficulty", "medium"),
                        "order": i + 1,
                    })
                return formatted_questions
        except json.JSONDecodeError as e:
            print(f"LLM 返回结果解析失败: {e}")
            print(f"返回内容: {result_text[:200]}...")
            
        return None
        
    except Exception as e:
        # 任何异常都返回 None，让调用方回退到固定题库
        print(f"LLM 生成面试题失败: {e}")
        return None
