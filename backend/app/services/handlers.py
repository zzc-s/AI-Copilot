"""核心业务同步处理：供路由与 Celery 任务共用。"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import ImprovementPlan, InterviewAnswer, InterviewQuestion, InterviewSession, JobDescription, JdSegment, Resume, ResumeMatchReport
from app.repositories.copilot_repo import get_jd, get_or_create_user, get_question, get_session, get_top_jd_segments
from app.services.cache import SimpleTTLCache
from app.services.embedding import cosine_score_unit_vectors, embed_texts, split_jd_chunks
from app.services.interview_engine import build_questions, evaluate_answer
from app.services.jd_parser import parse_jd
from app.services.llm_augment import augment_interview_questions, augment_parsed_jd, augment_plan, augment_rewrite_suggestions
from app.services.llm_client import LLMRouter
from app.services.plan_generator import generate_plan
from app.services.resume_matcher import match_resume_to_jd, structure_resume
from app.repositories.copilot_repo import save_llm_log
from app.schemas.copilot import InterviewAnswerRequest, InterviewQuestionOut, InterviewSessionCreateRequest, JDParseRequest, PlanGenerateRequest, ResumeMatchRequest

llm_router = LLMRouter()


def _weak_dimensions_for_session(db: Session, session_id: uuid.UUID) -> list[str]:
    stmt = (
        select(InterviewQuestion.dimension, InterviewAnswer.score)
        .join(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
        .where(InterviewQuestion.session_id == session_id)
    )
    out: list[str] = []
    seen: set[str] = set()
    for dim, score in db.execute(stmt).all():
        if not dim:
            continue
        if score is not None and float(score) < 72.0 and dim not in seen:
            seen.add(dim)
            out.append(str(dim))
    return out


def handle_jd_parse(db: Session, payload: JDParseRequest, cache: SimpleTTLCache) -> dict[str, Any]:
    key = f"jd:{payload.company}:{payload.role}:{hash(payload.raw_text)}"
    parsed = cache.get(key)
    if parsed is None:
        parsed = parse_jd(payload.raw_text, payload.role)
        parsed = augment_parsed_jd(
            parsed,
            role=payload.role,
            company=payload.company,
            raw_text=payload.raw_text,
        )
        llm_meta = llm_router.generate("jd_parse", {"role": payload.role})
        save_llm_log(
            db,
            "jd_parse",
            "v1",
            llm_meta["input_tokens"],
            llm_meta["output_tokens"],
            llm_meta["latency_ms"],
            model_name=llm_meta.get("model_name"),
        )
        cache.set(key, parsed)

    jd = JobDescription(
        source=payload.source,
        company=payload.company,
        role=payload.role,
        raw_text=payload.raw_text,
        parsed_json=parsed,
    )
    db.add(jd)
    db.flush()

    try:
        full_vecs, _ = embed_texts([payload.raw_text])
        if full_vecs:
            jd.embedding = full_vecs[0]
        chunks = split_jd_chunks(payload.raw_text)
        if chunks:
            chunk_vecs, _ = embed_texts(chunks)
            for i, txt in enumerate(chunks):
                vec = chunk_vecs[i] if i < len(chunk_vecs) else None
                db.add(JdSegment(jd_id=jd.id, chunk_index=i, text=txt, embedding=vec))
    except Exception:
        pass

    db.commit()
    db.refresh(jd)
    return {"jd_id": str(jd.id), "parsed": parsed}


def handle_resume_match(db: Session, payload: ResumeMatchRequest) -> dict[str, Any]:
    user = get_or_create_user(db, payload.user_email, payload.user_name)
    jd = get_jd(db, payload.jd_id)
    if not jd:
        raise ValueError("JD not found")

    resume = Resume(
        user_id=user.id,
        title=payload.resume_title,
        raw_text=payload.resume_text,
        structured_json=structure_resume(payload.resume_text),
    )
    db.add(resume)
    db.flush()

    vec_score: float | None = None
    evidence: list[str] = []
    try:
        rv, _ = embed_texts([payload.resume_text])
        if rv:
            resume.embedding = rv[0]
        if jd.embedding and rv:
            vec_score = cosine_score_unit_vectors(rv[0], jd.embedding)
        if rv:
            top_segs = get_top_jd_segments(db, jd.id, rv[0], k=3)
            evidence = [s.text[:300] for s in top_segs if s.text]
    except Exception:
        pass

    score, gap, rewrite = match_resume_to_jd(
        payload.resume_text,
        jd.parsed_json,
        jd_company=jd.company or "",
        jd_role=jd.role or "",
        vector_score=vec_score,
        jd_evidence=evidence or None,
    )
    rewrite = augment_rewrite_suggestions(rewrite, jd_parsed=jd.parsed_json, resume_text=payload.resume_text)
    report = ResumeMatchReport(
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        match_score=score,
        gap_json=gap,
        rewrite_suggestions_json=rewrite,
    )
    db.add(report)

    llm_meta = llm_router.generate("resume_match", {"resume_title": payload.resume_title})
    save_llm_log(
        db,
        "resume_match",
        "v1",
        llm_meta["input_tokens"],
        llm_meta["output_tokens"],
        llm_meta["latency_ms"],
        model_name=llm_meta.get("model_name"),
    )

    db.commit()
    db.refresh(report)
    return {
        "report_id": str(report.id),
        "match_score": report.match_score,
        "gap_analysis": report.gap_json,
        "rewrite_suggestions": report.rewrite_suggestions_json,
    }


def handle_interview_session(db: Session, payload: InterviewSessionCreateRequest) -> dict[str, Any]:
    user = get_or_create_user(db, payload.user_email, payload.user_name)
    jd = get_jd(db, payload.jd_id)
    if not jd:
        raise ValueError("JD not found")

    session = InterviewSession(user_id=user.id, jd_id=jd.id, status="started")
    db.add(session)
    db.flush()

    snippets: list[str] = []
    segs = (
        db.query(JdSegment)
        .filter(JdSegment.jd_id == jd.id)
        .order_by(JdSegment.chunk_index)
        .limit(5)
        .all()
    )
    snippets = [s.text for s in segs if s.text]

    qs_spec = build_questions(
        jd.role,
        jd_id=jd.id,
        jd_parsed=jd.parsed_json,
        jd_snippets=snippets or None,
        company=jd.company or "",
        jd_raw_text=jd.raw_text or "",
    )
    jd_excerpt = (" ".join(snippets)[:2000] if snippets else "") or (jd.raw_text or "")[:2000]
    qs_spec = augment_interview_questions(qs_spec, role=jd.role, jd_excerpt=jd_excerpt)
    for q in qs_spec:
        db.add(
            InterviewQuestion(
                session_id=session.id,
                question_text=q["question_text"],
                dimension=q["dimension"],
                difficulty=q["difficulty"],
            )
        )

    llm_meta = llm_router.generate("interview_questions", {"role": jd.role})
    save_llm_log(
        db,
        "interview_questions",
        "v1",
        llm_meta["input_tokens"],
        llm_meta["output_tokens"],
        llm_meta["latency_ms"],
        model_name=llm_meta.get("model_name"),
    )

    db.commit()
    db.refresh(session)
    questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session.id).all()
    return {
        "session_id": str(session.id),
        "questions": [InterviewQuestionOut.model_validate(q, from_attributes=True).model_dump(mode="json") for q in questions],
    }


def handle_answer(db: Session, session_id: uuid.UUID, payload: InterviewAnswerRequest) -> dict[str, Any]:
    session = get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    question = get_question(db, payload.question_id)
    if not question or str(question.session_id) != str(session.id):
        raise ValueError("Question not found in session")

    score, feedback = evaluate_answer(payload.answer_text)
    llm_meta = llm_router.generate("answer_eval", {"len": len(payload.answer_text)})
    save_llm_log(
        db,
        "answer_eval",
        "v1",
        llm_meta["input_tokens"],
        llm_meta["output_tokens"],
        llm_meta["latency_ms"],
        model_name=llm_meta.get("model_name"),
    )

    answer = InterviewAnswer(question_id=question.id, answer_text=payload.answer_text, score=score, feedback_json=feedback)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return {"answer_id": str(answer.id), "score": answer.score, "feedback": answer.feedback_json}


def handle_plan_generate(db: Session, payload: PlanGenerateRequest) -> dict[str, Any]:
    session = get_session(db, payload.session_id)
    if not session:
        raise ValueError("Session not found")
    user = get_or_create_user(db, payload.user_email, payload.user_email.split("@")[0])
    llm_meta = llm_router.generate("plan_generate", {"session_id": str(payload.session_id)})
    save_llm_log(
        db,
        "plan_generate",
        "v1",
        llm_meta["input_tokens"],
        llm_meta["output_tokens"],
        llm_meta["latency_ms"],
        model_name=llm_meta.get("model_name"),
    )

    report = db.scalar(
        select(ResumeMatchReport)
        .where(ResumeMatchReport.user_id == user.id, ResumeMatchReport.jd_id == session.jd_id)
        .order_by(desc(ResumeMatchReport.created_at))
    )
    gap = (report.gap_json or {}) if report else {}
    miss = list(gap.get("missing_keywords") or [])

    weak = _weak_dimensions_for_session(db, session.id)
    start_date, plan = generate_plan(
        session.overall_score,
        missing_keywords=miss,
        weak_dimensions=weak,
        session_id=session.id,
    )
    ctx = f"缺失关键词: {miss}\n薄弱维度: {weak}\n面试综合分: {session.overall_score}"
    plan = augment_plan(plan, context=ctx)
    plan_row = ImprovementPlan(user_id=user.id, session_id=session.id, plan_json=plan, start_date=start_date)
    db.add(plan_row)
    db.commit()
    db.refresh(plan_row)
    return {"plan_id": str(plan_row.id), "start_date": plan_row.start_date, "plan": plan_row.plan_json}


def handle_transcribe_answer(
    db: Session,
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    audio_bytes: bytes,
    mime_type: str,
) -> dict[str, Any]:
    from app.services.asr import transcribe_audio

    session = get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    question = get_question(db, question_id)
    if not question or str(question.session_id) != str(session.id):
        raise ValueError("Question not found in session")

    asr_out = transcribe_audio(audio_bytes, mime_type)
    text = (asr_out.get("text") or "").strip()
    if not text:
        raise RuntimeError("语音转写为空，请检查麦克风或稍后重试")

    score, feedback = evaluate_answer(text)
    feedback_m = dict(feedback)
    feedback_m["audio_meta"] = {
        "transcript": text,
        "model_name": asr_out.get("model_name"),
        "latency_ms": asr_out.get("latency_ms", 0),
    }

    llm_meta = llm_router.generate("asr_post", {"chars": len(text)})
    save_llm_log(
        db,
        "asr_post",
        "v1",
        llm_meta["input_tokens"],
        llm_meta["output_tokens"],
        llm_meta["latency_ms"],
        model_name=llm_meta.get("model_name"),
    )

    answer = InterviewAnswer(question_id=question.id, answer_text=text, score=score, feedback_json=feedback_m)
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return {
        "answer_id": str(answer.id),
        "score": answer.score,
        "feedback": answer.feedback_json,
        "transcript": text,
    }
