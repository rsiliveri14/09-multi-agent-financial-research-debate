"""Optional live HTTP tests against a running uvicorn process."""

from __future__ import annotations

import os

import httpx
import pytest

from data.benchmark import BENCHMARK

LIVE_URL = os.getenv("LIVE_API_URL", "http://127.0.0.1:8009")
HEADERS = {"Authorization": "Bearer dev-analyst-token", "Content-Type": "application/json"}

EXTRA_LOOKUPS = [
    ("What was Microsoft revenue in FY2024?", "MSFT"),
    ("What was NVIDIA Data Center revenue in FY2025?", "NVDA"),
    ("What was Tesla automotive gross margin in 2024?", "TSLA"),
    ("What was Amazon AWS operating income in 2024?", "AMZN"),
    ("What was Apple diluted EPS in FY2024?", "AAPL"),
    ("How much did Azure grow in FY2024?", "MSFT"),
    ("What were Tesla Q1 2025 deliveries?", "TSLA"),
    ("What was NVIDIA gross margin in Q1 FY2026?", "NVDA"),
]


def _ping() -> bool:
    try:
        response = httpx.get(f"{LIVE_URL}/health", timeout=1.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.live_http

require_live = pytest.mark.skipif(
    os.getenv("LIVE_HTTP") != "1" and not _ping(),
    reason="live API is not running (start make run-api or set LIVE_HTTP=1)",
)


@require_live
def test_live_http_health_ready_and_corpus():
    health = httpx.get(f"{LIVE_URL}/health", timeout=2.0)
    ready = httpx.get(f"{LIVE_URL}/ready", timeout=2.0)
    corpus = httpx.get(f"{LIVE_URL}/v1/corpus", headers=HEADERS, timeout=5.0)
    assert health.json()["status"] == "ok"
    assert ready.json()["status"] == "ready"
    assert ready.json()["chunks"] > 0
    assert set(corpus.json()["data"]["tickers"]) >= {"AAPL", "MSFT", "AMZN", "NVDA", "TSLA"}


@require_live
@pytest.mark.parametrize("item", BENCHMARK, ids=lambda item: item["id"])
def test_live_http_every_benchmark_debate(item):
    response = httpx.post(
        f"{LIVE_URL}/v1/debate",
        headers=HEADERS,
        json={"question": item["question"], "issuer_tickers": item.get("tickers") or []},
        timeout=60.0,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["errors"] == []
    data = body["data"]
    assert data["briefs"]
    assert data["synthesis"]["executive_summary"]
    assert data["graph"]["nodes"]
    request_id = data["request_id"]
    fetched = httpx.get(f"{LIVE_URL}/v1/debate/{request_id}", headers=HEADERS, timeout=10.0)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["request_id"] == request_id
    trace = httpx.get(f"{LIVE_URL}/v1/debate/{request_id}/trace", headers=HEADERS, timeout=10.0)
    assert any(event["event_type"] == "started" for event in trace.json()["data"]["events"])


@require_live
@pytest.mark.parametrize(
    "question,ticker",
    EXTRA_LOOKUPS,
    ids=[f"{ticker}-{index}" for index, (_question, ticker) in enumerate(EXTRA_LOOKUPS)],
)
def test_live_http_extra_lookups(question, ticker):
    response = httpx.post(
        f"{LIVE_URL}/v1/debate",
        headers=HEADERS,
        json={"question": question, "issuer_tickers": [ticker]},
        timeout=60.0,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    blob = data["synthesis"]["executive_summary"] + " ".join(
        claim["text"] for brief in data["briefs"] for claim in brief["claims"]
    )
    assert ticker in blob or any(claim.get("ticker") == ticker for brief in data["briefs"] for claim in brief["claims"])
