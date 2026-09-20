from domain.enums import AgentRole, Polarities
from domain.models import Claim
from services.claims import specialist_diversity, stance_from_claims
from services.disagreement import build_disagreement, contradiction_count


def _claim(role: AgentRole, topic: str, value: float | None, polarity: Polarities, cid: str) -> Claim:
    return Claim(
        id=cid,
        agent_role=role,
        topic_key=topic,
        text=f"{topic} {value}",
        polarity=polarity,
        confidence=0.7,
        value=value,
        ticker="AAPL",
        period="Q2FY2025",
        metric="net_sales",
    )


def test_disagreement_on_numeric_conflict():
    claims = [
        _claim(AgentRole.BULL, "AAPL.net_sales.Q2FY2025", 94.0, Polarities.POSITIVE, "b1"),
        _claim(AgentRole.BEAR, "AAPL.net_sales.Q2FY2025", 93.6, Polarities.NEGATIVE, "s1"),
    ]
    cells = build_disagreement(claims)
    assert contradiction_count(cells) == 1
    assert cells[0].status.value == "disagree"


def test_agreement_when_values_match():
    claims = [
        _claim(AgentRole.FINANCIAL, "AMZN.aws_sales.FY2024", 107.6, Polarities.POSITIVE, "f1"),
        _claim(AgentRole.EVIDENCE, "AMZN.aws_sales.FY2024", 107.6, Polarities.POSITIVE, "e1"),
    ]
    cells = build_disagreement(claims)
    assert cells[0].status.value == "agree"


def test_specialist_diversity_and_stance():
    briefs = []
    from domain.models import SpecialistBrief

    briefs.append(
        SpecialistBrief(
            role=AgentRole.BULL,
            stance=Polarities.POSITIVE,
            summary="x",
            claims=[_claim(AgentRole.BULL, "A.m.p", 1, Polarities.POSITIVE, "1")],
        )
    )
    briefs.append(
        SpecialistBrief(
            role=AgentRole.BEAR,
            stance=Polarities.NEGATIVE,
            summary="y",
            claims=[_claim(AgentRole.BEAR, "B.m.p", 2, Polarities.NEGATIVE, "2")],
        )
    )
    assert specialist_diversity(briefs) > 0.5
    assert stance_from_claims(briefs[0].claims) == Polarities.POSITIVE
