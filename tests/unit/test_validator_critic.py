from datetime import date
from uuid import uuid4

from domain.enums import AgentRole, Polarities
from domain.models import Citation, Claim
from services.critic import critique
from services.validator import apply_validations, validate_claims


def _claim(*, text: str, span: str, stale: bool = False, value: float | None = 94.0) -> Claim:
    return Claim(
        id="c1",
        agent_role=AgentRole.BULL,
        topic_key="AAPL.net_sales.Q2FY2025",
        text=text,
        polarity=Polarities.POSITIVE,
        confidence=0.7,
        value=value,
        ticker="AAPL",
        period="Q2FY2025",
        metric="net_sales",
        assumptions=["Growth rates persist into the next period."],
        citations=[
            Citation(
                document_id=uuid4(),
                page=8,
                section="MD&A",
                chunk_id=uuid4(),
                source_url="https://example.test",
                evidence_span=span,
                issuer_ticker="AAPL",
                document_type="10-Q",
                reporting_period="Q2FY2025",
                publication_date=date(2025, 5, 2),
            )
        ],
        stale_source=stale,
    )


def test_validator_supports_overlapping_numeric_claim():
    claim = _claim(
        text="Net sales for the second fiscal quarter of 2025 were $94.0 billion.",
        span="Net sales for the second fiscal quarter of 2025 were $94.0 billion, compared with $90.8 billion.",
    )
    results = validate_claims([claim])
    updated = apply_validations([claim], results)
    assert results[0].supported is True
    assert updated[0].supported is True


def test_validator_rejects_missing_citation():
    claim = _claim(text="Revenue was $1 billion.", span="unrelated")
    claim.citations = []
    results = validate_claims([claim])
    assert results[0].supported is False


def test_critic_flags_forward_looking_assumption():
    claim = _claim(
        text="Net sales for the second fiscal quarter of 2025 were $94.0 billion.",
        span="Net sales for the second fiscal quarter of 2025 were $94.0 billion.",
    )
    findings = critique([claim], [], [])
    assert any("Forward-looking" in item.attack for item in findings)
