from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.dashboard import DashboardAnalytics
from app.services.analytics import compute_dashboard
from app.services.auth import AuthUser, require_counsellor
from app.services.database import get_db

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/analytics", response_model=DashboardAnalytics)
def dashboard_analytics(
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    include_demo: bool = Query(default=True),
    _: AuthUser = Depends(require_counsellor),
):
    db = get_db()
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")

    now = datetime.now(timezone.utc)
    if not date_to:
        date_to = now.isoformat()
    if not date_from:
        date_from = (now - timedelta(days=30)).isoformat()

    leads = db.fetch_leads_for_analytics(date_from, date_to, include_demo=include_demo)
    brief_count = db.count_briefs(date_from, date_to)
    return compute_dashboard(leads, brief_count, date_from, date_to, include_demo)
