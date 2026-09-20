import pytest
from evaluation.evaluators.metrics import score_run

from data.benchmark import load_benchmark
from domain.models import DebateRequest


@pytest.mark.regression
@pytest.mark.parametrize("item", load_benchmark("regression"), ids=lambda item: item["id"])
async def test_every_regression_item_runs_live(runtime, item):
    result = await runtime.orchestrator.run(
        DebateRequest(question=item["question"], issuer_tickers=item.get("tickers") or [])
    )
    row = score_run(result, item)
    assert row["latency_ms"] >= 0
    assert 0.0 <= row["evidence_supported_accuracy"] <= 1.0
    assert result.briefs
    if item["id"] == "amzn-aws-fy2024":
        assert row["evidence_supported_accuracy"] >= 0.5
