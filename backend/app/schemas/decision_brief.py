from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class VerifiedFact(BaseModel):
    fact: str
    source_url: str
    last_verified_date: str


class DecisionBriefOutput(BaseModel):
    summary: str
    student_goals: list[str] = Field(default_factory=list)
    verified_facts: list[VerifiedFact] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    primary_objection: Optional[str] = None
    unresolved_questions: list[str] = Field(default_factory=list)
    questions_to_ask_counsellor: list[str] = Field(default_factory=list)
    recommended_next_step: str
    language: str
    verification_notice: str


class DecisionBriefRequest(BaseModel):
    lead_id: str


class DecisionBriefResponse(BaseModel):
    brief_id: str
    lead_id: str
    brief: DecisionBriefOutput


class DecisionBriefRecord(DecisionBriefResponse):
    created_at: str
    generation_status: str
