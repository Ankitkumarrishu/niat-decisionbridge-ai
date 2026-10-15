from __future__ import annotations

from app.services.database import DatabaseService, get_db


CONCERN_KEYWORDS: dict[str, list[str]] = {
    "fees": ["fee", "cost", "tuition", "budget", "scholarship"],
    "degree_university": ["degree", "university", "ugc", "award", "b.tech"],
    "curriculum": ["curriculum", "course", "ai", "learning", "phase"],
    "placements": ["placement", "job", "internship", "company", "hire"],
    "campus": ["campus", "city", "institution", "hostel", "location"],
    "admission_eligibility": ["admission", "eligibility", "nat", "apply", "enroll"],
    "scholarships": ["scholarship", "financial aid", "fee waiver"],
    "other": ["niat", "program", "support"],
}


def build_retrieval_query(intake: dict) -> str:
    parts = [
        intake.get("primary_concern", ""),
        intake.get("additional_question") or "",
        intake.get("preferred_campus") or "",
        intake.get("preferred_location") or "",
        intake.get("budget_range") or "",
        intake.get("education_status") or "",
    ]
    concern = intake.get("primary_concern") or "other"
    parts.extend(CONCERN_KEYWORDS.get(concern, []))
    return " ".join(p for p in parts if p).strip()


def retrieve_documents(intake: dict, db: DatabaseService | None = None) -> list[dict]:
    db = db or get_db()
    query = build_retrieval_query(intake)
    return db.search_knowledge(query, limit=8)
