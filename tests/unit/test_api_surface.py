"""API surface beyond the single happy-path debate."""

from tests.conftest import auth


async def test_metrics_prometheus(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert b"debate_runs_total" in response.content or b"python_info" in response.content or response.content


async def test_corpus_and_list_and_nodes(client):
    corpus = await client.get("/v1/corpus", headers=auth())
    assert corpus.status_code == 200
    tickers = corpus.json()["data"]["tickers"]
    assert set(tickers) >= {"AAPL", "MSFT", "AMZN", "NVDA", "TSLA"}
    listed = await client.get("/v1/debates", headers=auth())
    assert listed.status_code == 200
    nodes = await client.get("/v1/admin/nodes", headers=auth())
    catalog = nodes.json()["data"]
    for name in ("plan", "retrieve", "specialists", "critic", "validate", "synthesize"):
        assert name in catalog


async def test_missing_run_envelope(client):
    response = await client.get("/v1/debate/req_does_not_exist", headers=auth())
    assert response.status_code == 200
    body = response.json()
    assert body["errors"][0]["code"] == "NOT_FOUND"


async def test_invalid_token(client):
    response = await client.get("/v1/corpus", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


async def test_eval_requires_admin(client):
    denied = await client.post("/v1/eval/run?suite=regression", headers=auth("analyst"))
    assert denied.status_code == 403
    allowed = await client.post("/v1/eval/run?suite=regression", headers=auth("admin"))
    assert allowed.status_code == 200
    report = allowed.json()["data"]
    assert report["n"] == 6
    assert "multi_agent" in report
    latest = await client.get("/v1/eval/latest", headers=auth())
    assert latest.json()["data"]["n"] == 6


async def test_debate_rejects_overlong_question(client):
    response = await client.post("/v1/debate", json={"question": "x" * 2001}, headers=auth())
    assert response.status_code == 422


async def test_admin_can_clear_failure_flags(client):
    primed = await client.post("/v1/admin/simulate-failure", json={"empty_retrieval": True}, headers=auth("admin"))
    assert primed.json()["data"]["flags"]["empty_retrieval"] is True
    cleared = await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    assert cleared.json()["data"]["flags"] == {}
