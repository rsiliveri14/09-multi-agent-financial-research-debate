from domain.enums import AgentRole
from domain.errors import AuthorizationError
from tools.contracts import RetrieveInput, YoYInput


async def test_hybrid_retrieval_returns_ranked_chunks(runtime):
    hits = await runtime.retriever.search("Apple total net sales 391.0 billion 2024")
    assert hits
    assert hits[0].rank == 1
    assert "391.0" in hits[0].chunk.text or "Apple" in hits[0].chunk.issuer_ticker


async def test_tool_permission_denied(runtime):
    payload = YoYInput(current=10, prior=8)
    try:
        runtime.tools.yoy(AgentRole.BULL, payload)
        denied = False
    except AuthorizationError:
        denied = True
    assert denied


async def test_financial_may_call_yoy(runtime):
    result = runtime.tools.yoy(AgentRole.FINANCIAL, YoYInput(current=94.0, prior=90.8))
    assert result.direction == "up"
    assert result.change_pct > 0


async def test_retrieve_tool_contract(runtime):
    output = await runtime.tools.retrieve_filings(
        AgentRole.EVIDENCE,
        RetrieveInput(query="NVIDIA Data Center revenue 115.2", issuer_tickers=["NVDA"]),
    )
    assert output.latency_ms >= 0
    assert output.hits
