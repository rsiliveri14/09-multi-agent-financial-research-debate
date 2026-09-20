"""Curated debate benchmark. Gold labels are derived from the synthetic corpus."""

from __future__ import annotations

from typing import Any

BENCHMARK: list[dict[str, Any]] = [
    {
        "id": "aapl-fy2024-sales",
        "suite": "regression",
        "question": "What were Apple total net sales in FY2024, and did Greater China grow?",
        "tickers": ["AAPL"],
        "question_type": "mixed",
        "gold_facts": [
            {"topic": "AAPL.net_sales.FY2024", "value": 391.0, "unit": "billion"},
            {"topic": "AAPL.greater_china_sales.FY2024", "value": 67.0, "unit": "billion"},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "must_cite_sections": ["MD&A"],
        "notes": "Headline sales up, Greater China down vs 2023 $72.6B.",
    },
    {
        "id": "aapl-q2-preliminary-vs-10q",
        "suite": "regression",
        "question": "Apple Q2 FY2025 net sales: reconcile the 8-K preliminary figure versus the 10-Q.",
        "tickers": ["AAPL"],
        "question_type": "contradictory",
        "gold_facts": [
            {"topic": "AAPL.net_sales.Q2FY2025", "values": [93.6, 94.0], "prefer": 94.0},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "prefer_document": "10-Q",
        "notes": "8-K $93.6B vs 10-Q $94.0B.",
    },
    {
        "id": "msft-fy2024-cloud",
        "suite": "regression",
        "question": "How fast did Microsoft Azure grow in FY2024 and what was Intelligent Cloud revenue?",
        "tickers": ["MSFT"],
        "question_type": "lookup",
        "gold_facts": [
            {"topic": "MSFT.intelligent_cloud_revenue.FY2024", "value": 96.6, "unit": "billion"},
            {"topic": "MSFT.azure_growth.FY2024", "value": 30.0, "unit": "percent"},
        ],
        "expected_disagreement": False,
        "expected_unresolved_ok": True,
        "notes": "Primarily constructive cloud facts; risk agent should still flag Azure slowdown risk.",
    },
    {
        "id": "nvda-export-vs-datacenter",
        "suite": "regression",
        "question": "NVIDIA FY2025 Data Center revenue versus export-control risk for FY2026 visibility.",
        "tickers": ["NVDA"],
        "question_type": "mixed",
        "gold_facts": [
            {"topic": "NVDA.data_center_revenue.FY2025", "value": 115.2, "unit": "billion"},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "notes": "Bull: $115.2B Data Center. Bear/Risk: export controls reduce FY2026 visibility.",
    },
    {
        "id": "tsla-deliveries-8k-vs-10q",
        "suite": "regression",
        "question": "Tesla Q1 2025 deliveries: 8-K preliminary versus 10-Q, and what happened to automotive gross margin?",
        "tickers": ["TSLA"],
        "question_type": "contradictory",
        "gold_facts": [
            {"topic": "TSLA.vehicle_deliveries.Q1FY2025", "values": [310000.0, 336681.0], "prefer": 336681.0},
            {"topic": "TSLA.automotive_gross_margin.Q1FY2025", "value": 12.5, "unit": "percent"},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "prefer_document": "10-Q",
        "notes": "310k 8-K vs 336,681 10-Q; margin 12.5%.",
    },
    {
        "id": "amzn-aws-fy2024",
        "suite": "regression",
        "question": "What were Amazon net sales and AWS net sales in 2024?",
        "tickers": ["AMZN"],
        "question_type": "lookup",
        "gold_facts": [
            {"topic": "AMZN.net_sales.FY2024", "value": 638.0, "unit": "billion"},
            {"topic": "AMZN.aws_sales.FY2024", "value": 107.6, "unit": "billion"},
        ],
        "expected_disagreement": False,
        "expected_unresolved_ok": True,
        "notes": "Clean lookup.",
    },
    {
        "id": "tsla-auto-vs-energy",
        "suite": "full",
        "question": "Did Tesla grow in 2024? Contrast automotive revenue with energy storage.",
        "tickers": ["TSLA"],
        "question_type": "mixed",
        "gold_facts": [
            {"topic": "TSLA.automotive_revenue.FY2024", "value": 77.1, "unit": "billion"},
            {"topic": "TSLA.energy_revenue.FY2024", "value": 10.1, "unit": "billion"},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "notes": "Auto down vs 2023, energy up, total revenues slightly up.",
    },
    {
        "id": "aapl-unanswerable",
        "suite": "full",
        "question": "What is Apple's FY2030 iPhone unit guidance versus Samsung market share?",
        "tickers": ["AAPL"],
        "question_type": "unanswerable",
        "gold_facts": [],
        "expected_disagreement": False,
        "expected_unresolved_ok": True,
        "expect_insufficient": True,
        "notes": "Out of corpus.",
    },
    {
        "id": "nvda-q1fy2026-margin",
        "suite": "full",
        "question": "NVIDIA Q1 FY2026 revenue and gross margin versus FY2025 annual gross margin.",
        "tickers": ["NVDA"],
        "question_type": "temporal",
        "gold_facts": [
            {"topic": "NVDA.revenue.Q1FY2026", "value": 44.1, "unit": "billion"},
            {"topic": "NVDA.gross_margin.Q1FY2026", "value": 60.5, "unit": "percent"},
            {"topic": "NVDA.gross_margin.FY2025", "value": 75.0, "unit": "percent"},
        ],
        "expected_disagreement": True,
        "expected_unresolved_ok": True,
        "notes": "Revenue up sharply, margin down on product transition.",
    },
    {
        "id": "msft-vs-amzn-cloud",
        "suite": "full",
        "question": "Compare Microsoft Intelligent Cloud FY2024 revenue with Amazon AWS 2024 net sales.",
        "tickers": ["MSFT", "AMZN"],
        "question_type": "comparison",
        "gold_facts": [
            {"topic": "MSFT.intelligent_cloud_revenue.FY2024", "value": 96.6, "unit": "billion"},
            {"topic": "AMZN.aws_sales.FY2024", "value": 107.6, "unit": "billion"},
        ],
        "expected_disagreement": False,
        "expected_unresolved_ok": True,
        "notes": "AWS $107.6B vs Intelligent Cloud $96.6B; not like-for-like segments.",
    },
]


def load_benchmark(suite: str = "regression") -> list[dict[str, Any]]:
    if suite == "full":
        return list(BENCHMARK)
    if suite == "regression":
        return [item for item in BENCHMARK if item["suite"] == "regression"]
    raise ValueError(f"unknown suite {suite}")
