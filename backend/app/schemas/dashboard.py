from typing import Any, Optional

from pydantic import BaseModel, Field


class MetricRate(BaseModel):
    numerator: int
    denominator: int
    rate: Optional[float] = Field(
        description="Null when denominator is zero; otherwise ratio 0-1"
    )
    label: str


class ExperimentCohortMetrics(BaseModel):
    group: str
    eligible_leads: int
    briefs_generated: int
    follow_up_requests: int
    applications_completed: int
    applications_within_7_days: Optional[int] = None
    applications_within_7_days_note: str = ""


class DashboardAnalytics(BaseModel):
    date_from: str
    date_to: str
    total_consented_leads: int
    decision_briefs_generated: int
    counsellor_follow_up_requests: int
    completed_applications: int
    leads_by_primary_objection: dict[str, int]
    leads_by_language: dict[str, int]
    leads_by_follow_up_status: dict[str, int]
    brief_generation_success_rate: MetricRate
    lead_to_application_conversion_rate: MetricRate
    counsellor_follow_up_rate: MetricRate
    funnel: list[dict[str, Any]]
    time_series: list[dict[str, Any]]
    experiment_comparison: list[ExperimentCohortMetrics]
    demo_data_included: bool
    notes: list[str] = Field(default_factory=list)
