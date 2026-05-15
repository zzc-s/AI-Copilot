import base64
from uuid import UUID

from app.db.session import SessionLocal
from app.schemas.copilot import (
    InterviewAnswerRequest,
    InterviewSessionCreateRequest,
    JDParseRequest,
    PlanGenerateRequest,
    ResumeMatchRequest,
)
from app.services.cache import SimpleTTLCache
from app.services.handlers import (
    handle_answer,
    handle_interview_session,
    handle_jd_parse,
    handle_plan_generate,
    handle_resume_match,
    handle_transcribe_answer,
)
from app.tasks.celery_app import celery_app

_task_cache = SimpleTTLCache(ttl_seconds=3600)


@celery_app.task(name="tasks.jd_parse")
def task_jd_parse(payload: dict) -> dict:
    db = SessionLocal()
    try:
        p = JDParseRequest.model_validate(payload)
        data = handle_jd_parse(db, p, _task_cache)
        return {"status": "ok", "data": data}
    finally:
        db.close()


@celery_app.task(name="tasks.resume_match")
def task_resume_match(payload: dict) -> dict:
    db = SessionLocal()
    try:
        p = ResumeMatchRequest.model_validate(payload)
        data = handle_resume_match(db, p)
        return {"status": "ok", "data": data}
    finally:
        db.close()


@celery_app.task(name="tasks.interview_session")
def task_interview_session(payload: dict) -> dict:
    db = SessionLocal()
    try:
        p = InterviewSessionCreateRequest.model_validate(payload)
        data = handle_interview_session(db, p)
        return {"status": "ok", "data": data}
    finally:
        db.close()


@celery_app.task(name="tasks.answer")
def task_answer(session_id: str, payload: dict) -> dict:
    db = SessionLocal()
    try:
        p = InterviewAnswerRequest.model_validate(payload)
        data = handle_answer(db, UUID(session_id), p)
        return {"status": "ok", "data": data}
    finally:
        db.close()


@celery_app.task(name="tasks.plan_generate")
def task_plan_generate(payload: dict) -> dict:
    db = SessionLocal()
    try:
        p = PlanGenerateRequest.model_validate(payload)
        data = handle_plan_generate(db, p)
        out = dict(data)
        sd = out["start_date"]
        out["start_date"] = sd.isoformat() if hasattr(sd, "isoformat") else sd
        return {"status": "ok", "data": out}
    finally:
        db.close()


@celery_app.task(name="tasks.transcribe_answer")
def task_transcribe_answer(session_id: str, question_id: str, audio_b64: str, mime_type: str) -> dict:
    db = SessionLocal()
    try:
        raw = base64.b64decode(audio_b64)
        data = handle_transcribe_answer(db, UUID(session_id), UUID(question_id), raw, mime_type)
        return {"status": "ok", "data": data}
    finally:
        db.close()
