from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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


class ResumeMatchHistoryResponse(BaseModel):
    items: list[ResumeMatchHistoryItem]


class LatestPlanResponse(BaseModel):
    plan_id: UUID
    start_date: datetime
    plan: dict
