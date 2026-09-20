from tests.conftest import auth


async def test_empty_retrieval_partial(client):
    await client.post("/v1/admin/simulate-failure", json={"empty_retrieval": True}, headers=auth("admin"))
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024?"},
        headers=auth(),
    )
    await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    body = response.json()
    assert body["data"]["terminal_state"] in {"insufficient_evidence", "completed"}
    assert body["data"]["metrics"]["unsupported_claim_rate"] >= 0


async def test_provider_timeout_maps_status(client):
    await client.post("/v1/admin/simulate-failure", json={"provider_timeout": True}, headers=auth("admin"))
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024?"},
        headers=auth(),
    )
    await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    assert response.status_code in {200, 504}
    body = response.json()
    payload = body.get("data") or body
    terminal = payload.get("terminal_state") if isinstance(payload, dict) else None
    assert terminal == "provider_timeout" or (body.get("errors") and body["errors"][0]["code"] == "PROVIDER_TIMEOUT")


async def test_database_failure(client):
    await client.post("/v1/admin/simulate-failure", json={"database_failure": True}, headers=auth("admin"))
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024?"},
        headers=auth(),
    )
    await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    assert response.status_code == 503
    assert response.json()["errors"][0]["code"] == "DATABASE_FAILURE"


async def test_invalid_structured_output(client):
    await client.post("/v1/admin/simulate-failure", json={"invalid_structured_output": True}, headers=auth("admin"))
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024?"},
        headers=auth(),
    )
    await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    body = response.json()
    assert response.status_code in {200, 422}
    if response.status_code == 200:
        assert body["data"]["terminal_state"] == "validation_failed"
