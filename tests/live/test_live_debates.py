"""Live in-process debates against the real corpus and orchestrator (no mocks)."""

from __future__ import annotations

import pytest
from evaluation.evaluators.metrics import score_run
from tests.helpers import assert_live_debate

from data.benchmark import BENCHMARK
from domain.models import DebateRequest


@pytest.mark.live
@pytest.mark.parametrize("item", BENCHMARK, ids=lambda item: item["id"])
async def test_live_orchestrator_every_benchmark_question(runtime, item):
    result = await runtime.orchestrator.run(
        DebateRequest(
            question=item["question"],
            issuer_tickers=item.get("tickers") or [],
            include_single_agent=True,
        )
    )
    assert_live_debate(result, allow_empty=bool(item.get("expect_insufficient")))
    assert result.single_agent is not None
    row = score_run(result, item)
    assert 0.0 <= row["evidence_supported_accuracy"] <= 1.0
    assert 0.0 <= row["final_correctness"] <= 1.0
    if item.get("expect_insufficient"):
        assert result.terminal_state.value in {"insufficient_evidence", "completed", "unresolved"}


@pytest.mark.live
@pytest.mark.parametrize(
    "question,ticker",
    [
        ("What was Microsoft revenue in FY2024?", "MSFT"),
        ("What was NVIDIA Data Center revenue in FY2025?", "NVDA"),
        ("What was Tesla automotive gross margin in 2024?", "TSLA"),
        ("What was Amazon AWS operating income in 2024?", "AMZN"),
        ("What was Apple diluted EPS in FY2024?", "AAPL"),
        ("How much did Azure grow in FY2024?", "MSFT"),
        ("What were Tesla Q1 2025 deliveries?", "TSLA"),
        ("What was NVIDIA gross margin in Q1 FY2026?", "NVDA"),
        ("What were Amazon net sales in 2024?", "AMZN"),
        ("What was Tesla automotive revenue in 2024?", "TSLA"),
        ("What was NVIDIA Q1 FY2026 revenue?", "NVDA"),
        ("What was Apple iPhone net sales in FY2024?", "AAPL"),
    ],
)
async def test_live_lookup_questions_cite_ticker(runtime, question, ticker):
    result = await runtime.orchestrator.run(DebateRequest(question=question, issuer_tickers=[ticker]))
    assert_live_debate(result)
    blob = " ".join(claim.text for claim in result.claims) + result.synthesis.executive_summary
    assert ticker in blob or any(claim.ticker == ticker for claim in result.claims)
    assert any(citation.issuer_ticker == ticker for claim in result.claims for citation in claim.citations)
