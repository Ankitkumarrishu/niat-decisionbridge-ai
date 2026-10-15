from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.leads import (
    ApplicationStatusUpdate,
    FollowUpStatusUpdate,
    LeadDetail,
    LeadListResponse,
    LeadSummary,
)
from app.services.auth import AuthUser, require_counsellor
from app.services.database import DatabaseError, get_db

router = APIRouter(prefix="/api", tags=["leads"])


def _map_summary(row: dict) -> LeadSummary:
    return LeadSummary(
        id=row["id"],
        created_at=row["created_at"],
        student_first_name=row["student_first_name"],
        email=row.get("email"),
        education_status=row["education_status"],
        preferred_location=row.get("preferred_location"),
        preferred_campus=row.get("preferred_campus"),
        budget_range=row["budget_range"],
        primary_concern=row["primary_concern"],
        preferred_language=row["preferred_language"],
        follow_up_status=row["follow_up_status"],
        application_status=row["application_status"],
        primary_objection=row.get("primary_objection"),
        is_demo=row.get("is_demo", False),
        experiment_group=row.get("experiment_group"),
        latest_decision_brief_id=row.get("latest_decision_brief_id"),
    )


@router.get("/leads", response_model=LeadListResponse)
def list_leads(
    search: str | None = None,
    concern: str | None = None,
    language: str | None = None,
    follow_up_status: str | None = None,
    application_status: str | None = None,
    include_demo: bool = True,
    _: AuthUser = Depends(require_counsellor),
):
    db = get_db()
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")
    rows = db.list_leads(search, concern, language, follow_up_status, application_status, include_demo)
    items = [_map_summary(r) for r in rows]
    return LeadListResponse(items=items, total=len(items))


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def get_lead_detail(lead_id: str, _: AuthUser = Depends(require_counsellor)):
    db = get_db()
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")
    row = db.get_lead(lead_id)
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    brief = db.get_brief_for_lead(lead_id)
    events = db.list_events(lead_id)
    detail = LeadDetail(
        **_map_summary(row).model_dump(),
        additional_question=row.get("additional_question"),
        consent_storage=row.get("consent_storage", False),
        consent_followup=row.get("consent_followup", False),
        counsellor_notes=row.get("counsellor_notes"),
        next_action=row.get("next_action"),
        brief=brief,
        events=events,
    )
    return detail


@router.patch("/leads/{lead_id}/follow-up", response_model=LeadSummary)
def update_follow_up(
    lead_id: str,
    payload: FollowUpStatusUpdate,
    user: AuthUser = Depends(require_counsellor),
):
    db = get_db()
    row = db.get_lead(lead_id)
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    updates = {"follow_up_status": payload.follow_up_status}
    if payload.next_action is not None:
        updates["next_action"] = payload.next_action
    if payload.note:
        existing = row.get("counsellor_notes") or ""
        updates["counsellor_notes"] = (existing + "\n" + payload.note).strip()
    try:
        updated = db.update_lead(lead_id, updates)
        db.insert_event(
            lead_id,
            "follow_up_status_updated",
            {"status": payload.follow_up_status, "note": payload.note},
            created_by=user.email,
        )
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _map_summary(updated)


@router.patch("/leads/{lead_id}/application", response_model=LeadSummary)
def update_application(
    lead_id: str,
    payload: ApplicationStatusUpdate,
    user: AuthUser = Depends(require_counsellor),
):
    db = get_db()
    row = db.get_lead(lead_id)
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    updates: dict = {"application_status": payload.application_status}
    if payload.application_status == "completed":
        updates["application_completed_at"] = datetime.now(timezone.utc).isoformat()
        updates["follow_up_status"] = "application_completed"
    if payload.note:
        existing = row.get("counsellor_notes") or ""
        updates["counsellor_notes"] = (existing + "\n" + payload.note).strip()
    try:
        updated = db.update_lead(lead_id, updates)
        db.insert_event(
            lead_id,
            "application_status_updated",
            {"status": payload.application_status, "note": payload.note},
            created_by=user.email,
        )
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _map_summary(updated)
