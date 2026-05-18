from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class JDParseRequest(BaseModel):
    source: str = "manual"
    company: str
    role: str
    raw_text: str = Field(min_length=20)


class JDParseResponse(BaseModel):
    jd_id: UUID
    parsed: dict


class ResumeMatchRequest(BaseModel):
    user_email: str
    user_name: str
    resume_title: str
    resume_text: str
    jd_id: UUID


class ResumeMatchResponse(BaseModel):
    report_id: UUID
    match_score: float
    gap_analysis: dict
    rewrite_suggestions: dict


class InterviewSessionCreateRequest(BaseModel):
    user_email: str
    user_name: str
    jd_id: UUID


class InterviewQuestionOut(BaseModel):
    id: UUID
    question_text: str
    dimension: str
    difficulty: str


class InterviewSessionCreateResponse(BaseModel):
    session_id: UUID
    questions: list[InterviewQuestionOut]


class InterviewAnswerRequest(BaseModel):
    question_id: UUID
    answer_text: str = Field(min_length=1)


class InterviewAnswerResponse(BaseModel):
    answer_id: UUID
    score: float
    feedback: dict


class InterviewReportResponse(BaseModel):
    session_id: UUID
    status: str
    overall_score: float | None
    summary: str | None
    questions_answered: int


class PlanGenerateRequest(BaseModel):
    user_email: str
    session_id: UUID


class PlanGenerateResponse(BaseModel):
    plan_id: UUID
    start_date: datetime
    plan: dict


class ResumeMatchHistoryItem(BaseModel):
    report_id: UUID
    match_score: float
    created_at: datetime
    jd_id: UUID | None = None
    company: str | None = None
    role: str | None = None


class ResumeMatchHistoryResponse(BaseModel):
    items: list[ResumeMatchHistoryItem]


class InterviewHistoryItem(BaseModel):
    session_id: UUID
    jd_id: UUID
    status: str
    overall_score: float | None
    created_at: datetime
    company: str | None = None
    role: str | None = None


class PlanHistoryItem(BaseModel):
    plan_id: UUID
    session_id: UUID
    start_date: datetime
    created_at: datetime
    company: str | None = None
    role: str | None = None


PaginatedResumeMatchHistory = PaginatedResponse[ResumeMatchHistoryItem]
PaginatedInterviewHistory = PaginatedResponse[InterviewHistoryItem]
PaginatedPlanHistory = PaginatedResponse[PlanHistoryItem]


class UserHistoryResponse(BaseModel):
    user_email: str
    match_reports: list[ResumeMatchHistoryItem]
    interview_sessions: list[InterviewHistoryItem]
    plans: list[PlanHistoryItem]


class LatestPlanResponse(BaseModel):
    plan_id: UUID
    start_date: datetime
    plan: dict
