import base64
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import ImprovementPlan, LlmLog, ResumeMatchReport
from app.repositories.copilot_repo import get_or_create_user, get_session, session_scores
from app.schemas.copilot import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewQuestionOut,
    InterviewReportResponse,
    InterviewSessionCreateRequest,
    InterviewSessionCreateResponse,
    JDParseRequest,
    JDParseResponse,
    LatestPlanResponse,
    PlanGenerateRequest,
    PlanGenerateResponse,
    ResumeMatchHistoryItem,
    ResumeMatchHistoryResponse,
    ResumeMatchRequest,
    ResumeMatchResponse,
)
from app.services.cache import SimpleTTLCache
from app.services.celery_health import broker_available
from app.services.handlers import (
    handle_answer,
    handle_interview_session,
    handle_jd_parse,
    handle_plan_generate,
    handle_resume_match,
    handle_transcribe_answer,
)
from app.services.sync_task_store import get_sync_task_response, put_celery_style_result
from app.services.interview_engine import summarize_session
from app.tasks.celery_app import celery_app
from app.tasks.jobs import (
    task_answer,
    task_interview_session,
    task_jd_parse,
    task_plan_generate,
    task_resume_match,
    task_transcribe_answer,
)

router = APIRouter()
cache = SimpleTTLCache(ttl_seconds=settings.cache_ttl_seconds)


def _task_result(async_result: AsyncResult) -> dict:
    body: dict = {"task_id": async_result.id, "status": async_result.state}
    if async_result.ready():
        if async_result.failed():
            body["error"] = str(async_result.result)
        else:
            body["result"] = async_result.result
    return body


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict:
    if task_id.startswith("sync-"):
        hit = get_sync_task_response(task_id)
        if hit is not None:
            return hit
        raise HTTPException(status_code=404, detail="Task not found or expired (sync tasks are in-memory only)")
    return _task_result(AsyncResult(task_id, app=celery_app))


@router.get("/llm/logs")
def llm_logs(limit: int = 50, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(LlmLog).order_by(desc(LlmLog.created_at)).limit(limit)).all()
    return [
        {
            "scene": r.scene,
            "model_name": r.model_name,
            "prompt_version": r.prompt_version,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "latency_ms": r.latency_ms,
            "cost_estimate": r.cost_estimate,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/llm/stats")
def llm_stats(days: int = 7, db: Session = Depends(get_db)) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(
            LlmLog.model_name,
            LlmLog.scene,
            func.count().label("cnt"),
            func.avg(LlmLog.latency_ms).label("avg_latency_ms"),
            func.sum(LlmLog.cost_estimate).label("total_cost"),
        )
        .where(LlmLog.created_at >= since)
        .group_by(LlmLog.model_name, LlmLog.scene)
    )
    rows = db.execute(stmt).all()
    out = []
    for r in rows:
        out.append(
            {
                "model_name": r.model_name or "unknown",
                "scene": r.scene,
                "call_count": int(r.cnt),
                "avg_latency_ms": float(r.avg_latency_ms or 0),
                "total_cost": float(r.total_cost or 0),
            }
        )
    return out


@router.post("/admin/backfill")
def admin_backfill(db: Session = Depends(get_db)) -> dict:
    from app.services.backfill import backfill_jd_embeddings

    return backfill_jd_embeddings(db)


@router.post("/jd/parse")
def parse_job_description(
    payload: JDParseRequest,
    db: Session = Depends(get_db),
    async_mode: bool = Query(False, alias="async"),
):
    if async_mode and broker_available():
        try:
            ar = task_jd_parse.delay(payload.model_dump(mode="json"))
            return {"task_id": ar.id}
        except Exception:
            pass
    try:
        out = handle_jd_parse(db, payload, cache)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if async_mode:
        tid = put_celery_style_result({"status": "ok", "data": out})
        return {"task_id": tid}
    return JDParseResponse(jd_id=UUID(out["jd_id"]), parsed=out["parsed"])


@router.post("/resume/match")
def match_resume(
    payload: ResumeMatchRequest,
    db: Session = Depends(get_db),
    async_mode: bool = Query(False, alias="async"),
):
    if async_mode and broker_available():
        try:
            ar = task_resume_match.delay(payload.model_dump(mode="json"))
            return {"task_id": ar.id}
        except Exception:
            pass
    try:
        out = handle_resume_match(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if async_mode:
        tid = put_celery_style_result({"status": "ok", "data": out})
        return {"task_id": tid}
    return ResumeMatchResponse(
        report_id=UUID(out["report_id"]),
        match_score=out["match_score"],
        gap_analysis=out["gap_analysis"],
        rewrite_suggestions=out["rewrite_suggestions"],
    )


@router.post("/interview/session")
def create_interview_session(
    payload: InterviewSessionCreateRequest,
    db: Session = Depends(get_db),
    async_mode: bool = Query(False, alias="async"),
):
    if async_mode:
        ar = task_interview_session.delay(payload.model_dump(mode="json"))
        return {"task_id": ar.id}
    try:
        out = handle_interview_session(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    qs = [InterviewQuestionOut.model_validate(q) for q in out["questions"]]
    return InterviewSessionCreateResponse(session_id=UUID(out["session_id"]), questions=qs)


@router.post("/interview/{session_id}/answer")
def answer_question(
    session_id: UUID,
    payload: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    async_mode: bool = Query(False, alias="async"),
):
    if async_mode and broker_available():
        try:
            ar = task_answer.delay(str(session_id), payload.model_dump(mode="json"))
            return {"task_id": ar.id}
        except Exception:
            pass
    try:
        out = handle_answer(db, session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if async_mode:
        tid = put_celery_style_result({"status": "ok", "data": out})
        return {"task_id": tid}
    return InterviewAnswerResponse(answer_id=UUID(out["answer_id"]), score=out["score"], feedback=out["feedback"])


@router.post("/interview/{session_id}/answer/audio")
async def answer_audio(
    session_id: UUID,
    question_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    b64 = base64.b64encode(data).decode("ascii")
    mime = file.content_type or "application/octet-stream"
    if broker_available():
        try:
            ar = task_transcribe_answer.delay(str(session_id), str(question_id), b64, mime)
            return {"task_id": ar.id}
        except Exception:
            pass
    try:
        out = handle_transcribe_answer(db, session_id, question_id, data, mime)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    tid = put_celery_style_result({"status": "ok", "data": out})
    return {"task_id": tid}


@router.get("/interview/{session_id}/report", response_model=InterviewReportResponse)
def report(session_id: UUID, db: Session = Depends(get_db)) -> InterviewReportResponse:
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    scores = session_scores(db, session.id)
    overall, summary = summarize_session(scores)
    session.overall_score = overall
    session.summary = summary
    session.status = "completed" if scores else session.status
    db.add(session)
    db.commit()
    return InterviewReportResponse(
        session_id=session.id,
        status=session.status,
        overall_score=session.overall_score,
        summary=session.summary,
        questions_answered=len(scores),
    )


@router.post("/plan/generate")
def create_plan(
    payload: PlanGenerateRequest,
    db: Session = Depends(get_db),
    async_mode: bool = Query(False, alias="async"),
):
    if async_mode and broker_available():
        try:
            ar = task_plan_generate.delay(payload.model_dump(mode="json"))
            return {"task_id": ar.id}
        except Exception:
            pass
    try:
        out = handle_plan_generate(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if async_mode:
        out2 = dict(out)
        sd = out2["start_date"]
        out2["start_date"] = sd.isoformat() if hasattr(sd, "isoformat") else sd
        tid = put_celery_style_result({"status": "ok", "data": out2})
        return {"task_id": tid}
    return PlanGenerateResponse(plan_id=UUID(out["plan_id"]), start_date=out["start_date"], plan=out["plan"])


@router.get("/resume/match/history", response_model=ResumeMatchHistoryResponse)
def resume_match_history(user_email: str, db: Session = Depends(get_db)) -> ResumeMatchHistoryResponse:
    user = get_or_create_user(db, user_email, user_email.split("@")[0])
    rows = db.scalars(select(ResumeMatchReport).where(ResumeMatchReport.user_id == user.id).order_by(desc(ResumeMatchReport.created_at)).limit(20)).all()
    return ResumeMatchHistoryResponse(items=[ResumeMatchHistoryItem(report_id=r.id, match_score=r.match_score, created_at=r.created_at) for r in rows])


@router.get("/plan/latest", response_model=LatestPlanResponse)
def latest_plan(user_email: str, db: Session = Depends(get_db)) -> LatestPlanResponse:
    user = get_or_create_user(db, user_email, user_email.split("@")[0])
    row = db.scalar(select(ImprovementPlan).where(ImprovementPlan.user_id == user.id).order_by(desc(ImprovementPlan.created_at)))
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    return LatestPlanResponse(plan_id=row.id, start_date=row.start_date, plan=row.plan_json)
