from datetime import date
from uuid import uuid4

from domain.enums import AgentRole, AgreementStatus, Polarities
from domain.models import Citation, Claim, DisagreementCell
from services.resolution import resolve_conflicts


def test_resolution_prefers_10q_over_8k():
    ten_q = Claim(
        id="q",
        agent_role=AgentRole.FINANCIAL,
        topic_key="AAPL.net_sales.Q2FY2025",
        text="Net sales were $94.0 billion.",
        polarity=Polarities.NEUTRAL,
        confidence=0.8,
        value=94.0,
        ticker="AAPL",
        period="Q2FY2025",
        metric="net_sales",
        citations=[
            Citation(
                document_id=uuid4(),
                page=8,
                section="MD&A",
                chunk_id=uuid4(),
                source_url="u",
                evidence_span="Net sales were $94.0 billion",
                document_type="10-Q",
                publication_date=date(2025, 5, 2),
            )
        ],
    )
    eight_k = Claim(
        id="k",
        agent_role=AgentRole.BEAR,
        topic_key="AAPL.net_sales.Q2FY2025",
        text="Preliminary net sales were $93.6 billion.",
        polarity=Polarities.NEGATIVE,
        confidence=0.6,
        value=93.6,
        ticker="AAPL",
        period="Q2FY2025",
        metric="net_sales",
        stale_source=True,
        citations=[
            Citation(
                document_id=uuid4(),
                page=1,
                section="Item 2.02",
                chunk_id=uuid4(),
                source_url="u",
                evidence_span="Preliminary net sales were $93.6 billion",
                document_type="8-K",
                publication_date=date(2025, 5, 1),
            )
        ],
    )
    cell = DisagreementCell(
        topic_key="AAPL.net_sales.Q2FY2025",
        metric="net_sales",
        ticker="AAPL",
        period="Q2FY2025",
        status=AgreementStatus.DISAGREE,
        agreement_score=0.2,
        claim_ids=["q", "k"],
    )
    claims, resolved, unresolved = resolve_conflicts([ten_q, eight_k], [cell])
    assert "AAPL.net_sales.Q2FY2025" in resolved
    assert not unresolved
    assert claims[1].supported is False
