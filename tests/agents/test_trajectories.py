from tests.helpers import assert_live_debate

from domain.models import DebateRequest


async def test_mixed_apple_debate_has_disagreement(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(question="What were Apple total net sales in FY2024, and did Greater China grow?")
    )
    assert_live_debate(result)
    assert result.metrics.contradiction_count >= 1 or any(
        cell.status.value == "disagree" for cell in result.disagreement
    )


async def test_contradictory_8k_vs_10q_not_forced(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(question="Apple Q2 FY2025 net sales: reconcile the 8-K preliminary figure versus the 10-Q.")
    )
    assert result.terminal_state.value in {"unresolved", "completed", "insufficient_evidence"}
    texts = " ".join(claim.text for claim in result.claims)
    assert "93.6" in texts or "94.0" in texts
    if result.metrics.contradiction_count == 0:
        assert result.synthesis.unresolved or any(claim.stale_source for claim in result.claims)


async def test_single_agent_baseline_present(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(question="What were Amazon net sales and AWS net sales in 2024?", include_single_agent=True)
    )
    assert result.single_agent is not None
    assert result.single_agent.answer


async def test_nvda_export_risk_trajectory(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(question="NVIDIA FY2025 Data Center revenue versus export-control risk for FY2026 visibility.")
    )
    assert_live_debate(result)
    blob = " ".join(claim.text.lower() for claim in result.claims)
    assert "115.2" in blob or "data center" in blob
    assert "export" in blob or any(brief.role.value == "risk" and brief.claims for brief in result.briefs)


async def test_tesla_margin_and_energy_trajectory(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(question="Did Tesla grow in 2024? Contrast automotive revenue with energy storage.")
    )
    assert_live_debate(result)
    tickers = {claim.ticker for claim in result.claims}
    assert "TSLA" in tickers


async def test_msft_amzn_comparison_trajectory(runtime):
    result = await runtime.orchestrator.run(
        DebateRequest(
            question="Compare Microsoft Intelligent Cloud FY2024 revenue with Amazon AWS 2024 net sales.",
            issuer_tickers=["MSFT", "AMZN"],
        )
    )
    assert_live_debate(result)
    found = {claim.ticker for claim in result.claims}
    assert "MSFT" in found or "AMZN" in found
