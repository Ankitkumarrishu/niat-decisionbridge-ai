from app.schemas.decision_brief import DecisionBriefOutput, VerifiedFact
from app.services.ai_service import AIService


def test_citation_enforcement_drops_invented_urls():
    service = AIService()
    brief = DecisionBriefOutput(
        summary="Fees are ₹2 lakh",
        verified_facts=[
            VerifiedFact(
                fact="Invented fee",
                source_url="https://invented.example/fees",
                last_verified_date="2026-01-01",
            )
        ],
        recommended_next_step="Confirm with NIAT",
        language="en",
        verification_notice="old",
    )
    snippets = [
        {
            "source_url": "https://www.niatindia.com/campus",
            "verification_status": "verified",
        }
    ]
    cleaned = service._enforce_citation_integrity(brief, snippets, "en")
    assert cleaned.verified_facts == []
    assert "Insufficient verified" in cleaned.unresolved_questions[0]


def test_citation_enforcement_keeps_allowed_urls():
    service = AIService()
    url = "https://www.niatindia.com/campus"
    brief = DecisionBriefOutput(
        summary="NIAT is not a university",
        verified_facts=[
            VerifiedFact(
                fact="NIAT is not a degree-awarding body",
                source_url=url,
                last_verified_date="2026-03-15",
            )
        ],
        recommended_next_step="Confirm admission with the university",
        language="en",
        verification_notice="old",
    )
    cleaned = service._enforce_citation_integrity(brief, [{"source_url": url}], "en")
    assert len(cleaned.verified_facts) == 1
    assert cleaned.source_references == [url]
