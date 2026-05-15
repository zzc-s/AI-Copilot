# 下一阶段能力（实现顺序）

与《求职 AI Copilot 实施计划》中第 2 阶段一致，建议按依赖从底到上推进：

1. **向量检索增强（RAG / pgvector）**  
   PostgreSQL 启用 `pgvector`，为 JD/简历存储 embedding；匹配与面试上下文增加「相似片段召回」。

2. **异步队列**  
   长耗时任务（解析、匹配、评分）走 Celery + Redis；API 返回 task_id，前端轮询或 SSE 拉取结果。

3. **多模型路由**  
   在 `llm_client` 上按场景与成本选择主备模型、重试与熔断；`llm_logs` 记录 `model_name` 供对比与成本分析。

4. **语音面试**  
   浏览器录音上传 → 转写服务（如 Whisper）→ 复用现有文本面试评分链；`MockInterview` 增加语音模式 UI。

每一阶段可单独开需求/PR，避免与 UI 大改揉在同一分支。
