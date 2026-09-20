from domain.enums import AgentRole, AgreementStatus, Polarities, TerminalState
from domain.models import Claim, CriticFinding, DisagreementCell, SpecialistBrief
from services.claims import normalize_claims, unique_topics
from services.synthesis import synthesize


def _claim(role: AgentRole, topic: str, cid: str, supported: bool = True) -> Claim:
    return Claim(
        id=cid,
        agent_role=role,
        topic_key=topic,
        text=f"{topic} cited from MD&A",
        polarity=Polarities.POSITIVE,
        confidence=0.8,
        ticker=topic.split(".")[0],
        period="FY2024",
        metric=topic.split(".")[1],
        supported=supported,
        validation_score=0.7,
    )


def test_normalize_and_unique_topics():
    brief = SpecialistBrief(
        role=AgentRole.BULL,
        stance=Polarities.POSITIVE,
        summary="s",
        claims=[_claim(AgentRole.BULL, "AAPL.net_sales.FY2024", "b1")],
    )
    claims = normalize_claims([brief])
    assert unique_topics(claims) == ["AAPL.net_sales.FY2024"]


def test_synthesis_abstains_without_support():
    report = synthesize("q", [], [], [], [], [])
    assert report.outcome == TerminalState.INSUFFICIENT_EVIDENCE
    assert report.confidence <= 0.15


def test_synthesis_keeps_unresolved():
    claims = [_claim(AgentRole.BULL, "AAPL.net_sales.Q2FY2025", "b1")]
    cells = [
        DisagreementCell(
            topic_key="AAPL.net_sales.Q2FY2025",
            metric="net_sales",
            ticker="AAPL",
            period="Q2FY2025",
            status=AgreementStatus.DISAGREE,
            agreement_score=0.2,
            claim_ids=["b1"],
        )
    ]
    findings = [
        CriticFinding(
            claim_id="b1",
            agent_role=AgentRole.BULL,
            severity="high",
            attack="stale 8-K",
            recommendation="prefer 10-Q",
        )
    ]
    briefs = [
        SpecialistBrief(role=AgentRole.BULL, stance=Polarities.POSITIVE, summary="s", claims=claims, confidence=0.6)
    ]
    report = synthesize("Apple Q2", claims, cells, findings, briefs, ["AAPL.net_sales.Q2FY2025"])
    assert report.outcome == TerminalState.UNRESOLVED
    assert report.unresolved
