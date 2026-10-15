from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.limiter import limiter
from app.schemas.decision_brief import DecisionBriefRequest, DecisionBriefResponse
from app.services.ai_service import AIServiceError, get_ai_service
from app.services.database import DatabaseError, get_db
from app.services.retrieval import retrieve_documents

router = APIRouter(prefix="/api", tags=["decision-brief"])


@router.post("/decision-brief", response_model=DecisionBriefResponse)
@limiter.limit("10/minute")
def generate_decision_brief(request: Request, payload: DecisionBriefRequest):
    db = get_db()
    ai = get_ai_service()

    if not db.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env.",
        )

    try:
        lead = db.get_lead(payload.lead_id)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not lead.get("consent_storage"):
        raise HTTPException(status_code=400, detail="Lead did not consent to storage")

    documents = retrieve_documents(lead, db)
    if not documents:
        raise HTTPException(
            status_code=503,
            detail="Verified knowledge base is empty. Run supabase/seed.sql.",
        )

    snippets = [
        {
            "source_url": d.get("source_url"),
            "verification_status": d.get("verification_status"),
        }
        for d in documents
    ]
    lang = lead.get("preferred_language", "en")

    try:
        brief = ai.generate_brief(lead, documents)
        brief = ai._enforce_citation_integrity(brief, snippets, lang)
    except AIServiceError as exc:
        status_code = 503 if exc.code in {"ai_not_configured", "ai_call_failed"} else 502
        raise HTTPException(
            status_code=status_code,
            detail=f"{exc}. Your intake was saved as lead {payload.lead_id}; retry brief generation without resubmitting.",
        ) from exc

    now = datetime.now(timezone.utc).isoformat()
    brief_row = {
        "lead_id": lead["id"],
        "summary": brief.summary,
        "student_goals": brief.student_goals,
        "verified_facts": [f.model_dump() for f in brief.verified_facts],
        "source_references": brief.source_references,
        "primary_objection": brief.primary_objection or lead.get("primary_concern"),
        "unresolved_questions": brief.unresolved_questions,
        "questions_to_ask_counsellor": brief.questions_to_ask_counsellor,
        "recommended_next_step": brief.recommended_next_step,
        "language": brief.language,
        "verification_notice": brief.verification_notice,
        "generation_status": "success",
    }

    try:
        saved = db.insert_brief(brief_row)
        updates = {
            "latest_decision_brief_id": saved["id"],
            "follow_up_status": "brief_generated",
            "brief_generated_at": now,
            "primary_objection": brief.primary_objection or lead.get("primary_concern"),
        }
        if lead.get("consent_followup"):
            updates["follow_up_status"] = "follow_up_requested"
        db.update_lead(lead["id"], updates)
        db.insert_event(lead["id"], "brief_generated", {"brief_id": saved["id"]})
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return DecisionBriefResponse(brief_id=saved["id"], lead_id=lead["id"], brief=brief)


@router.get("/decision-brief/{brief_id}", response_model=DecisionBriefResponse)
def get_decision_brief(brief_id: str):
    db = get_db()
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")
    row = db.get_brief(brief_id)
    if not row or row.get("generation_status") != "success":
        raise HTTPException(status_code=404, detail="Brief not found")
    from app.schemas.decision_brief import DecisionBriefOutput

    brief = DecisionBriefOutput(
        summary=row["summary"],
        student_goals=row.get("student_goals") or [],
        verified_facts=row.get("verified_facts") or [],
        source_references=row.get("source_references") or [],
        primary_objection=row.get("primary_objection"),
        unresolved_questions=row.get("unresolved_questions") or [],
        questions_to_ask_counsellor=row.get("questions_to_ask_counsellor") or [],
        recommended_next_step=row["recommended_next_step"],
        language=row["language"],
        verification_notice=row["verification_notice"],
    )
    return DecisionBriefResponse(brief_id=row["id"], lead_id=row["lead_id"], brief=brief)
