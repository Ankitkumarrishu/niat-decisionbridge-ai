from app.services.analytics import compute_dashboard


def test_analytics_calculations():
    leads = [
        {
            "consent_storage": True,
            "is_eligible_lead": True,
            "brief_generated_at": "2026-01-02T00:00:00Z",
            "consent_followup": True,
            "application_status": "completed",
            "primary_concern": "fees",
            "primary_objection": "fees",
            "preferred_language": "en",
            "follow_up_status": "application_completed",
            "created_at": "2026-01-01T00:00:00Z",
            "experiment_group": "treatment",
            "experiment_enrolled_at": "2026-01-01T00:00:00Z",
            "application_completed_at": "2026-01-05T00:00:00Z",
        },
        {
            "consent_storage": True,
            "is_eligible_lead": True,
            "brief_generated_at": None,
            "consent_followup": False,
            "application_status": "not_started",
            "primary_concern": "campus",
            "preferred_language": "hi",
            "follow_up_status": "new",
            "created_at": "2026-01-03T00:00:00Z",
            "experiment_group": "control",
            "experiment_enrolled_at": "2026-01-03T00:00:00Z",
        },
    ]
    result = compute_dashboard(leads, brief_count=1, date_from="2026-01-01", date_to="2026-01-31", include_demo=False)
    assert result.total_consented_leads == 2
    assert result.brief_generation_success_rate.rate == 0.5
    assert result.lead_to_application_conversion_rate.rate == 0.5
    assert result.counsellor_follow_up_rate.rate == 0.5
