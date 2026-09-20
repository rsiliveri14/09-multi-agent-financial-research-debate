"""Live FastAPI debates through the ASGI app (real runtime, no mocked specialists)."""

from __future__ import annotations

import pytest
from tests.conftest import auth
from tests.helpers import assert_live_debate

from data.benchmark import BENCHMARK
from domain.models import DebateResult


@pytest.mark.live
@pytest.mark.parametrize("item", BENCHMARK, ids=lambda item: item["id"])
async def test_live_api_debate_roundtrip(client, item):
    response = await client.post(
        "/v1/debate",
        json={"question": item["question"], "issuer_tickers": item.get("tickers") or []},
        headers=auth(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["errors"] == []
    data = body["data"]
    result = DebateResult.model_validate(data)
    assert_live_debate(result, allow_empty=bool(item.get("expect_insufficient")))
    request_id = data["request_id"]
    fetched = await client.get(f"/v1/debate/{request_id}", headers=auth())
    assert fetched.status_code == 200
    assert fetched.json()["data"]["request_id"] == request_id
    trace = await client.get(f"/v1/debate/{request_id}/trace", headers=auth())
    events = trace.json()["data"]["events"]
    assert any(event["event_type"] == "started" for event in events)
    assert any(event["node"] == "synthesize" for event in events)
    graph = await client.get(f"/v1/debate/{request_id}/graph", headers=auth())
    assert graph.json()["data"]["nodes"]
