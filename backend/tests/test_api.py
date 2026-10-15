import jwt
from datetime import datetime, timedelta, timezone

from app.schemas.decision_brief import DecisionBriefOutput, VerifiedFact


def _counsellor_headers():
    payload = {
        "sub": "user-1",
        "email": "counsellor@test.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "test-jwt-secret-for-unit-tests-only", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


def test_invalid_intake_payload(client, mock_db):
    res = client.post("/api/intake", json={"student_first_name": ""})
    assert res.status_code == 422


def test_missing_consent_rejected(client, mock_db):
    payload = {
        "student_first_name": "Asha",
        "education_status": "in_class_12",
        "budget_range": "undecided",
        "primary_concern": "fees",
        "preferred_language": "en",
        "consent_storage": False,
    }
    res = client.post("/api/intake", json=payload)
    assert res.status_code == 422


def test_valid_intake(client, mock_db):
    mock_db.create_lead.return_value = {"id": "lead-1"}
    payload = {
        "student_first_name": "Asha",
        "education_status": "in_class_12",
        "budget_range": "undecided",
        "primary_concern": "fees",
        "preferred_language": "en",
        "consent_storage": True,
        "consent_followup": False,
    }
    res = client.post("/api/intake", json=payload)
    assert res.status_code == 201
    assert res.json()["lead_id"] == "lead-1"


def test_ai_not_configured(client, mock_db):
    mock_db.get_lead.return_value = {
        "id": "lead-1",
        "consent_storage": True,
        "primary_concern": "fees",
        "preferred_language": "en",
    }
    mock_db.search_knowledge.return_value = [
        {
            "id": "doc-1",
            "title": "Test",
            "category": "general",
            "content": "NIAT is an upskilling initiative.",
            "source_url": "https://www.niatindia.com/",
            "last_verified_date": "2026-03-15",
            "verification_status": "verified",
        }
    ]
    res = client.post("/api/decision-brief", json={"lead_id": "lead-1"})
    assert res.status_code == 503
    assert "OpenAI" in res.json()["detail"]


def test_ai_output_validation(client, mock_db, monkeypatch):
    from app.services import ai_service

    mock_db.get_lead.return_value = {
        "id": "lead-1",
        "consent_storage": True,
        "student_first_name": "Asha",
        "primary_concern": "fees",
        "preferred_language": "en",
    }
    mock_db.search_knowledge.return_value = [
        {
            "id": "doc-1",
            "title": "Disclaimer",
            "category": "general",
            "content": "NIAT is not a degree-awarding body.",
            "source_url": "https://www.niatindia.com/campus",
            "last_verified_date": "2026-03-15",
            "verification_status": "verified",
        }
    ]

    def fake_generate(self, intake, documents):
        return DecisionBriefOutput(
            summary="Summary",
            verified_facts=[
                VerifiedFact(
                    fact="NIAT is not a degree-awarding body.",
                    source_url="https://www.niatindia.com/campus",
                    last_verified_date="2026-03-15",
                )
            ],
            source_references=["https://www.niatindia.com/campus"],
            recommended_next_step="Speak with a counsellor",
            language="en",
            verification_notice="Prototype notice",
        )

    monkeypatch.setattr(ai_service.AIService, "generate_brief", fake_generate)
    monkeypatch.setattr(ai_service.AIService, "is_configured", lambda self: True)

    mock_db.insert_brief.return_value = {"id": "brief-1"}
    mock_db.update_lead.return_value = {"id": "lead-1"}

    res = client.post("/api/decision-brief", json={"lead_id": "lead-1"})
    assert res.status_code == 200
    assert res.json()["brief_id"] == "brief-1"


def test_unsupported_facts_stripped(client, mock_db, monkeypatch):
    from app.services import ai_service

    mock_db.get_lead.return_value = {
        "id": "lead-1",
        "consent_storage": True,
        "student_first_name": "Asha",
        "primary_concern": "fees",
        "preferred_language": "en",
    }
    mock_db.search_knowledge.return_value = [
        {
            "id": "doc-1",
            "title": "Disclaimer",
            "category": "general",
            "content": "NIAT is not a degree-awarding body.",
            "source_url": "https://www.niatindia.com/campus",
            "last_verified_date": "2026-03-15",
            "verification_status": "verified",
        }
    ]

    def fake_generate(self, intake, documents):
        return DecisionBriefOutput(
            summary="Summary with invented fee ₹2 lakh",
            verified_facts=[
                VerifiedFact(
                    fact="Invented fee claim",
                    source_url="https://fake.example/fees",
                    last_verified_date="2026-03-15",
                )
            ],
            recommended_next_step="Confirm fees with NIAT",
            language="en",
            verification_notice="Notice",
        )

    monkeypatch.setattr(ai_service.AIService, "generate_brief", fake_generate)
    monkeypatch.setattr(ai_service.AIService, "is_configured", lambda self: True)
    mock_db.insert_brief.return_value = {"id": "brief-2"}
    mock_db.update_lead.return_value = {"id": "lead-1"}

    res = client.post("/api/decision-brief", json={"lead_id": "lead-1"})
    assert res.status_code == 200
    facts = res.json()["brief"]["verified_facts"]
    assert facts == []


def test_database_write_failure(client, mock_db):
    from app.services.database import DatabaseError

    mock_db.create_lead.side_effect = DatabaseError("Failed to create lead")
    res = client.post(
        "/api/intake",
        json={
            "student_first_name": "Asha",
            "education_status": "in_class_12",
            "budget_range": "undecided",
            "primary_concern": "fees",
            "preferred_language": "en",
            "consent_storage": True,
        },
    )
    assert res.status_code == 503
    assert "Failed to create lead" in res.json()["detail"]


def test_forbidden_counsellor(client, mock_db):
    payload = {
        "sub": "user-2",
        "email": "not-allowed@test.com",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "test-jwt-secret-for-unit-tests-only", algorithm="HS256")
    res = client.get("/api/leads", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_database_not_configured(client):
    res = client.post(
        "/api/intake",
        json={
            "student_first_name": "Asha",
            "education_status": "in_class_12",
            "budget_range": "undecided",
            "primary_concern": "fees",
            "preferred_language": "en",
            "consent_storage": True,
        },
    )
    assert res.status_code == 503


def test_unauthorized_crm(client, mock_db):
    res = client.get("/api/leads")
    assert res.status_code == 401


def test_valid_follow_up_update(client, mock_db):
    mock_db.get_lead.return_value = {"id": "lead-1", "counsellor_notes": ""}
    mock_db.update_lead.return_value = {
        "id": "lead-1",
        "created_at": "2026-01-01T00:00:00Z",
        "student_first_name": "Demo",
        "education_status": "other",
        "budget_range": "undecided",
        "primary_concern": "fees",
        "preferred_language": "en",
        "follow_up_status": "contacted",
        "application_status": "not_started",
    }
    res = client.patch(
        "/api/leads/lead-1/follow-up",
        json={"follow_up_status": "contacted", "note": "Called student"},
        headers=_counsellor_headers(),
    )
    assert res.status_code == 200
    assert res.json()["follow_up_status"] == "contacted"


def test_analytics_zero_leads(client, mock_db):
    mock_db.fetch_leads_for_analytics.return_value = []
    mock_db.count_briefs.return_value = 0
    res = client.get("/api/dashboard/analytics", headers=_counsellor_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["total_consented_leads"] == 0
    assert body["brief_generation_success_rate"]["rate"] is None
