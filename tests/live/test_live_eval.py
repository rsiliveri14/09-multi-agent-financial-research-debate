"""Run the evaluation harness live against the in-process corpus."""

from __future__ import annotations

import pytest
from evaluation.runners.harness import run_suite


@pytest.mark.live
async def test_live_regression_eval_harness(runtime):
    report = await run_suite("regression", runtime)
    assert report["n"] == 6
    assert len([row for row in report["rows"] if row["mode"] == "multi_agent"]) == 6
    assert report["multi_agent"]["final_correctness"] >= 0.0
    assert report["single_agent"]["final_correctness"] >= 0.0


@pytest.mark.live
async def test_live_full_eval_harness(runtime):
    report = await run_suite("full", runtime)
    assert report["n"] == 10
    assert len([row for row in report["rows"] if row["mode"] == "multi_agent"]) == 10
    assert set(row["id"] for row in report["rows"] if row["mode"] == "multi_agent") == {
        "aapl-fy2024-sales",
        "aapl-q2-preliminary-vs-10q",
        "msft-fy2024-cloud",
        "nvda-export-vs-datacenter",
        "tsla-deliveries-8k-vs-10q",
        "amzn-aws-fy2024",
        "tsla-auto-vs-energy",
        "aapl-unanswerable",
        "nvda-q1fy2026-margin",
        "msft-vs-amzn-cloud",
    }
