from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import (
    ImprovementPlan,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    JobDescription,
    JdSegment,
    LlmLog,
    Resume,
    ResumeMatchReport,
    User,
)
from app.services.embedding import cosine_score_unit_vectors


def get_or_create_user(db: Session, email: str, name: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, name=name)
    db.add(user)
    db.flush()
    return user


def get_jd(db: Session, jd_id: UUID) -> JobDescription | None:
    return db.get(JobDescription, jd_id)


def get_session(db: Session, session_id: UUID) -> InterviewSession | None:
    return db.get(InterviewSession, session_id)


def get_question(db: Session, question_id: UUID) -> InterviewQuestion | None:
    return db.get(InterviewQuestion, question_id)


def get_top_jd_segments(db: Session, jd_id: UUID, query_vec: list[float], k: int = 3) -> list[JdSegment]:
    rows = list(db.scalars(select(JdSegment).where(JdSegment.jd_id == jd_id)).all())
    if not query_vec or not rows:
        return rows[:k]

    def score(row: JdSegment) -> float:
        if row.embedding is None:
            return -1.0
        return cosine_score_unit_vectors(query_vec, list(row.embedding))

    return sorted(rows, key=score, reverse=True)[:k]


def session_scores(db: Session, session_id: UUID) -> list[float]:
    rows = db.scalars(
        select(InterviewAnswer.score).join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id).where(
            InterviewQuestion.session_id == session_id
        )
    ).all()
    return [float(score) for score in rows]


def save_llm_log(
    db: Session,
    scene: str,
    prompt_version: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    model_name: str | None = None,
) -> None:
    cost_estimate = round((input_tokens + output_tokens) / 1_000_000 * 2.0, 6)
    db.add(
        LlmLog(
            scene=scene,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            model_name=model_name,
        )
    )


__all__ = [
    "get_or_create_user",
    "get_jd",
    "get_session",
    "get_question",
    "get_top_jd_segments",
    "session_scores",
    "save_llm_log",
    "ImprovementPlan",
    "InterviewAnswer",
    "InterviewQuestion",
    "InterviewSession",
    "JobDescription",
    "Resume",
    "ResumeMatchReport",
]
