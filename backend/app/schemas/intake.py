from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class EducationStatus(str, Enum):
    completed_class_12 = "completed_class_12"
    in_class_12 = "in_class_12"
    other = "other"


class BudgetRange(str, Enum):
    undecided = "undecided"
    below_5_lakh = "below_5_lakh"
    range_5_10_lakh = "5_10_lakh"
    above_10_lakh = "above_10_lakh"


class PrimaryConcern(str, Enum):
    fees = "fees"
    degree_university = "degree_university"
    curriculum = "curriculum"
    placements = "placements"
    campus = "campus"
    admission_eligibility = "admission_eligibility"
    scholarships = "scholarships"
    other = "other"


class PreferredLanguage(str, Enum):
    en = "en"
    hi = "hi"


class IntakeSubmission(BaseModel):
    student_first_name: str = Field(min_length=1, max_length=80)
    email: Optional[EmailStr] = None
    education_status: EducationStatus
    preferred_location: Optional[str] = Field(default=None, max_length=120)
    preferred_campus: Optional[str] = Field(default=None, max_length=200)
    budget_range: BudgetRange
    primary_concern: PrimaryConcern
    additional_question: Optional[str] = Field(default=None, max_length=2000)
    preferred_language: PreferredLanguage
    consent_storage: bool = False
    consent_followup: bool = False
    source_identifier: Optional[str] = Field(default=None, max_length=120)
    campaign_identifier: Optional[str] = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_consent_and_email(self):
        if not self.consent_storage:
            raise ValueError("consent_storage is required to submit intake")
        if self.consent_followup and not self.email:
            raise ValueError("email is required when requesting counsellor follow-up")
        return self


class IntakeResponse(BaseModel):
    lead_id: str
    experiment_group: str
    message: str
