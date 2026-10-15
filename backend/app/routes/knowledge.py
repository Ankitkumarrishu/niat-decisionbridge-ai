from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.knowledge import KnowledgeDocument, KnowledgeSearchResponse
from app.services.auth import AuthUser, require_counsellor
from app.services.database import get_db

router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    q: str = Query(default="", max_length=200),
    _: AuthUser = Depends(require_counsellor),
):
    db = get_db()
    if not db.is_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")
    rows = db.search_knowledge(q)
    results = [
        KnowledgeDocument(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            content=r["content"],
            source_url=r["source_url"],
            last_verified_date=str(r["last_verified_date"]),
            verification_status=r["verification_status"],
            campus_or_university_id=r.get("campus_or_university_id"),
        )
        for r in rows
    ]
    return KnowledgeSearchResponse(query=q, results=results)
