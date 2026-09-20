from domain.models import DebateResult


def assert_live_debate(result: DebateResult, *, allow_empty: bool = False) -> None:
    assert result.request_id
    assert result.question
    assert result.plan.question_type
    roles = {brief.role.value for brief in result.briefs}
    assert {"bull", "bear", "financial", "risk", "evidence"} <= roles
    assert result.graph.nodes
    assert result.synthesis.executive_summary
    assert result.metrics.latency_ms >= 0
    assert result.metrics.estimated_cost_usd >= 0
    if not allow_empty:
        assert any(brief.claims for brief in result.briefs)
        cited = [claim for claim in result.claims if claim.citations]
        assert cited, "live debate must attach filing citations"
