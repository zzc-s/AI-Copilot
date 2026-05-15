import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

if settings.pgvector_enabled:
    from pgvector.sqlalchemy import Vector

    def _embedding_column():
        return mapped_column(Vector(settings.embedding_dim), nullable=True)
else:

    def _embedding_column():
        return mapped_column(JSONB, nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    embedding: Mapped[list[float] | None] = _embedding_column()


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(255), default="manual", nullable=False)
    company: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    embedding: Mapped[list[float] | None] = _embedding_column()
    segments: Mapped[list["JdSegment"]] = relationship(back_populates="jd", cascade="all, delete-orphan")


class JdSegment(Base):
    __tablename__ = "jd_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jd_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = _embedding_column()
    jd: Mapped["JobDescription"] = relationship(back_populates="segments")


class ResumeMatchReport(Base):
    __tablename__ = "resume_match_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    jd_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    gap_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    rewrite_suggestions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    jd_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="started", nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    dimension: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False)
    session: Mapped["InterviewSession"] = relationship(back_populates="questions")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_questions.id"), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ImprovementPlan(Base):
    __tablename__ = "improvement_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    plan_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LlmLog(Base):
    __tablename__ = "llm_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
