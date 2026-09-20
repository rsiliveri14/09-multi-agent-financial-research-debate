from tests.conftest import auth


async def test_tool_timeout_failure(client):
    await client.post("/v1/admin/simulate-failure", json={"tool_timeout": True}, headers=auth("admin"))
    response = await client.post(
        "/v1/debate",
        json={"question": "What were Apple total net sales in FY2024?"},
        headers=auth(),
    )
    await client.post("/v1/admin/simulate-failure", json={}, headers=auth("admin"))
    assert response.status_code in {200, 502}
    body = response.json()
    if response.status_code == 200:
        assert body["data"]["terminal_state"] == "tool_failure"
    else:
        assert body["errors"][0]["code"] == "TOOL_FAILURE"


async def test_malformed_json(client):
    response = await client.post(
        "/v1/debate", content="{not-json", headers={**auth(), "Content-Type": "application/json"}
    )
    assert response.status_code in {400, 422}
