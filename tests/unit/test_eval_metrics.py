from evaluation.evaluators.metrics import number_in_text, numeric_accuracy, score_run

from domain.enums import AgentRole, Polarities, QuestionType, RunStatus, TerminalState
from domain.models import Claim, DebateMetrics, DebateResult, ProvenanceGraph, ResearchPlan, SynthesisReport


def _result(texts: list[str], values: list[float], terminal: TerminalState = TerminalState.COMPLETED) -> DebateResult:
    claims = [
        Claim(
            id=f"c{i}",
            agent_role=AgentRole.FINANCIAL,
            topic_key="AAPL.net_sales.FY2024",
            text=text,
            polarity=Polarities.POSITIVE,
            confidence=0.8,
            value=value,
            ticker="AAPL",
            period="FY2024",
            metric="net_sales",
            supported=True,
        )
        for i, (text, value) in enumerate(zip(texts, values, strict=True), start=1)
    ]
    return DebateResult(
        request_id="req_eval",
        status=RunStatus.COMPLETED,
        question="q",
        plan=ResearchPlan(question="q", question_type=QuestionType.LOOKUP),
        claims=claims,
        synthesis=SynthesisReport(headline="h", executive_summary=" ".join(texts), outcome=terminal),
        graph=ProvenanceGraph(),
        metrics=DebateMetrics(),
        terminal_state=terminal,
    )


def test_number_in_text_and_accuracy():
    assert number_in_text(391.0, "Total net sales were 391.0 billion")
    result = _result(["Total net sales were 391.0 billion"], [391.0])
    gold = [{"topic": "AAPL.net_sales.FY2024", "value": 391.0}]
    assert numeric_accuracy(result, gold) == 1.0
    row = score_run(result, {"id": "x", "gold_facts": gold, "expected_disagreement": False})
    assert row["final_correctness"] == 1.0


def test_insufficient_gold_scores_abstention():
    result = _result(["no numbers"], [0.0], terminal=TerminalState.INSUFFICIENT_EVIDENCE)
    result.claims = []
    assert numeric_accuracy(result, []) == 1.0
    row = score_run(result, {"id": "u", "gold_facts": [], "expect_insufficient": True})
    assert row["final_correctness"] == 1.0
