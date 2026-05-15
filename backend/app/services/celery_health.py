"""检测 Celery broker（Redis）是否可达；不可达时异步接口降级为同步执行。"""

from __future__ import annotations

import logging

from app.core.config import settings

_log = logging.getLogger(__name__)


def broker_available(timeout: float = 0.6) -> bool:
    try:
        from kombu import Connection

        conn = Connection(settings.celery_broker_url)
        try:
            conn.ensure_connection(max_retries=1, timeout=timeout)
        finally:
            conn.release()
        return True
    except Exception as exc:
        _log.debug("Celery broker unavailable: %s", exc)
        return False
