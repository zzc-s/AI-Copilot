from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "copilot",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    broker_connection_retry_on_startup=True,
)

import app.tasks.jobs  # noqa: E402,F401
