from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from data.benchmark import load_benchmark
from domain.models import DebateRequest
from evaluation.evaluators.metrics import number_in_text, score_run
from services.runtime import AppRuntime, build_runtime


async def run_suite(suite: str, runtime: AppRuntime | None = None) -> dict[str, Any]:
    runtime = runtime or await build_runtime()
    items = load_benchmark(suite)
    rows: list[dict[str, Any]] = []
    for item in items:
        request = DebateRequest(
            question=item["question"], issuer_tickers=item.get("tickers") or [], include_single_agent=True
        )
        result = await runtime.orchestrator.run(request, request_id=f"eval_{item['id']}")
        row = score_run(result, item)
        row["mode"] = "multi_agent"
        rows.append(row)
        if result.single_agent is not None:
            baseline = {
                "id": item["id"],
                "mode": "single_agent",
                "evidence_supported_accuracy": row["evidence_supported_accuracy"] * 0.0
                + _single_accuracy(result, item),
                "unsupported_claims": sum(1 for claim in result.single_agent.claims if claim.supported is False)
                / max(1, len(result.single_agent.claims)),
                "contradiction_detection": 0.0 if item.get("expected_disagreement") else 1.0,
                "final_correctness": _single_accuracy(result, item),
                "specialist_diversity": 0.0,
                "redundant_tool_use": 0,
                "latency_ms": result.single_agent.latency_ms,
                "cost_usd": result.single_agent.estimated_cost_usd,
                "terminal_state": "abstained" if result.single_agent.abstained else "completed",
            }
            rows.append(baseline)
    multi = [row for row in rows if row["mode"] == "multi_agent"]
    single = [row for row in rows if row["mode"] == "single_agent"]
    summary = {
        "suite": suite,
        "n": len(items),
        "multi_agent": _aggregate(multi),
        "single_agent": _aggregate(single) if single else {},
        "quality_delta": _delta(_aggregate(multi), _aggregate(single) if single else {}),
        "rows": rows,
    }
    return summary


def _single_accuracy(result: Any, item: dict[str, Any]) -> float:
    gold = item.get("gold_facts") or []
    if item.get("expect_insufficient"):
        return 1.0 if result.single_agent and result.single_agent.abstained else 0.0
    if not gold or result.single_agent is None:
        return 0.0
    blob = result.single_agent.answer + " " + " ".join(claim.text for claim in result.single_agent.claims)
    hits = 0
    for fact in gold:
        expected = fact.get("prefer", fact.get("value"))
        values = fact.get("values") or ([expected] if expected is not None else [])
        if any(number_in_text(float(value), blob) for value in values if value is not None):
            hits += 1
    return hits / len(gold)


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}

    def mean(key: str) -> float:
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        return round(sum(values) / len(values), 4) if values else 0.0

    latencies = [int(row["latency_ms"]) for row in rows]
    return {
        "evidence_supported_accuracy": mean("evidence_supported_accuracy"),
        "unsupported_claim_rate": mean("unsupported_claims"),
        "contradiction_detection": mean("contradiction_detection"),
        "final_correctness": mean("final_correctness"),
        "specialist_diversity": mean("specialist_diversity"),
        "redundant_tool_use": mean("redundant_tool_use"),
        "latency_ms_p50": _percentile(latencies, 50),
        "latency_ms_p95": _percentile(latencies, 95),
        "latency_ms_p99": _percentile(latencies, 99),
        "cost_usd_mean": mean("cost_usd"),
    }


def _percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = int(round((q / 100) * (len(ordered) - 1)))
    return ordered[rank]


def _delta(multi: dict[str, Any], single: dict[str, Any]) -> dict[str, Any]:
    if not single:
        return {}
    keys = [
        "evidence_supported_accuracy",
        "final_correctness",
        "contradiction_detection",
        "latency_ms_p50",
        "cost_usd_mean",
    ]
    return {key: round(float(multi.get(key) or 0) - float(single.get(key) or 0), 4) for key in keys}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="regression", choices=["regression", "full"])
    parser.add_argument("--out", default="evaluation/reports/regression.json")
    args = parser.parse_args()
    report = asyncio.run(run_suite(args.suite))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("suite", "n", "multi_agent", "single_agent", "quality_delta")}, indent=2))


if __name__ == "__main__":
    main()
