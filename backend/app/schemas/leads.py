from typing import Any, Optional

from pydantic import BaseModel, Field


class LeadSummary(BaseModel):
    id: str
    created_at: str
    student_first_name: str
    email: Optional[str] = None
    education_status: str
    preferred_location: Optional[str] = None
    preferred_campus: Optional[str] = None
    budget_range: str
    primary_concern: str
    preferred_language: str
    follow_up_status: str
    application_status: str
    primary_objection: Optional[str] = None
    is_demo: bool = False
    experiment_group: Optional[str] = None
    latest_decision_brief_id: Optional[str] = None


class LeadDetail(LeadSummary):
    additional_question: Optional[str] = None
    consent_storage: bool
    consent_followup: bool
    counsellor_notes: Optional[str] = None
    next_action: Optional[str] = None
    brief: Optional[dict[str, Any]] = None
    events: list[dict[str, Any]] = Field(default_factory=list)


class LeadListResponse(BaseModel):
    items: list[LeadSummary]
    total: int


class FollowUpStatusUpdate(BaseModel):
    follow_up_status: str = Field(
        pattern="^(new|brief_generated|follow_up_requested|contacted|application_completed|closed)$"
    )
    note: Optional[str] = Field(default=None, max_length=2000)
    next_action: Optional[str] = Field(default=None, max_length=500)


class ApplicationStatusUpdate(BaseModel):
    application_status: str = Field(pattern="^(not_started|in_progress|completed|withdrawn)$")
    note: Optional[str] = Field(default=None, max_length=2000)
