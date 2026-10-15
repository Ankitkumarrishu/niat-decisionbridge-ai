from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    settings = get_settings()
    missing = settings.missing_settings()
    return {
        "status": "ok",
        "service": "NIAT DecisionBridge AI",
        "openai_configured": settings.openai_configured(),
        "supabase_configured": settings.supabase_configured(),
        "auth_configured": settings.auth_configured(),
        "counsellor_allowlist_configured": bool(settings.counsellor_email_set),
        "missing_settings": missing,
        "ready_for_intake": settings.supabase_configured(),
        "ready_for_ai": settings.openai_configured() and settings.supabase_configured(),
    }
