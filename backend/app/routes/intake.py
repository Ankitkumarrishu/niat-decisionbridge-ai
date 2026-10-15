import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.limiter import limiter
from app.schemas.intake import IntakeResponse, IntakeSubmission
from app.services.database import DatabaseError, get_db

router = APIRouter(prefix="/api", tags=["intake"])


@router.post("/intake", response_model=IntakeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def submit_intake(request: Request, payload: IntakeSubmission):
    settings = get_settings()
    db = get_db()
    if not db.is_configured():
        missing = ", ".join(settings.missing_settings()) or "SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                f"in backend/.env then restart the API. Currently missing: {missing}."
            ),
        )

    ratio = settings.experiment_treatment_ratio
    experiment_group = "treatment" if random.random() < ratio else "control"
    now = datetime.now(timezone.utc).isoformat()

    row = {
        "student_first_name": payload.student_first_name.strip(),
        "email": str(payload.email) if payload.email else None,
        "education_status": payload.education_status.value,
        "preferred_location": payload.preferred_location,
        "preferred_campus": payload.preferred_campus,
        "budget_range": payload.budget_range.value,
        "primary_concern": payload.primary_concern.value,
        "additional_question": payload.additional_question,
        "preferred_language": payload.preferred_language.value,
        "consent_storage": True,
        "consent_followup": payload.consent_followup,
        "follow_up_status": "new",
        "application_status": "not_started",
        "is_demo": False,
        "experiment_group": experiment_group,
        "experiment_enrolled_at": now,
        "is_eligible_lead": True,
        "source_identifier": payload.source_identifier,
        "campaign_identifier": payload.campaign_identifier,
    }

    try:
        lead = db.create_lead(row)
        db.insert_event(
            lead["id"],
            "intake_submitted",
            {"experiment_group": experiment_group, "consent_followup": payload.consent_followup},
        )
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return IntakeResponse(
        lead_id=lead["id"],
        experiment_group=experiment_group,
        message="Intake saved. Generate your decision brief next.",
    )
