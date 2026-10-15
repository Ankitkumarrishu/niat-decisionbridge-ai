from pydantic import BaseModel


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    category: str
    content: str
    source_url: str
    last_verified_date: str
    verification_status: str
    campus_or_university_id: str | None = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeDocument]
