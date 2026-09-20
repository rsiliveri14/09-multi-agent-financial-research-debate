from tests.conftest import auth


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready(client):
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_debate_requires_auth(client):
    response = await client.post("/v1/debate", json={"question": "What were Apple total net sales in FY2024?"})
    assert response.status_code == 401
    body = response.json()
    assert body["errors"][0]["code"] == "AUTHENTICATION_FAILURE"


async def test_debate_rejects_short_question(client):
    response = await client.post("/v1/debate", json={"question": "no"}, headers=auth())
    assert response.status_code == 422


async def test_debate_happy_path(client):
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024, and did Greater China grow?"},
        headers=auth(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"completed", "partial"}
    data = body["data"]
    assert data["briefs"]
    assert data["synthesis"]["executive_summary"]
    assert data["graph"]["nodes"]
    request_id = data["request_id"]
    trace = await client.get(f"/v1/debate/{request_id}/trace", headers=auth())
    assert trace.status_code == 200
    graph = await client.get(f"/v1/debate/{request_id}/graph", headers=auth())
    assert graph.status_code == 200


async def test_admin_denied_to_analyst(client):
    response = await client.post("/v1/admin/simulate-failure", json={"empty_retrieval": True}, headers=auth("analyst"))
    assert response.status_code == 403
