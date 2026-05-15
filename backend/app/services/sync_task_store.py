"""broker 不可用时，异步接口同步执行并将结果存入内存，供 GET /tasks/{id} 一次性取出（进程重启后失效）。"""

from __future__ import annotations

import uuid
from typing import Any

# task_id -> GET /tasks 响应体（与 Celery SUCCESS 形状一致）
_SYNC_RESULTS: dict[str, dict[str, Any]] = {}


def put_celery_style_result(task_return: dict[str, Any]) -> str:
    """task_return 与 Celery 任务返回值一致，例如 {\"status\": \"ok\", \"data\": {...}}。"""
    tid = f"sync-{uuid.uuid4()}"
    _SYNC_RESULTS[tid] = {
        "task_id": tid,
        "status": "SUCCESS",
        "result": task_return,
    }
    return tid


def get_sync_task_response(task_id: str) -> dict[str, Any] | None:
    """供轮询多次读取，不删除（仅开发/单进程；生产应使用真 broker）。"""
    return _SYNC_RESULTS.get(task_id)
