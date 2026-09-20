from __future__ import annotations

import time

from domain.enums import AgentRole
from domain.errors import AuthorizationError, ToolFailureError
from services.retrieval import HybridRetriever
from tools.contracts import TOOL_PERMISSIONS, RetrieveInput, RetrieveOutput, YoYInput, YoYOutput


class ToolRouter:
    def __init__(self, retriever: HybridRetriever, timeout_seconds: float = 6.0) -> None:
        self.retriever = retriever
        self.timeout_seconds = timeout_seconds

    def authorize(self, role: AgentRole, tool_name: str) -> None:
        allowed = TOOL_PERMISSIONS.get(role, set())
        if tool_name not in allowed:
            raise AuthorizationError(f"role {role.value} cannot call {tool_name}")

    async def retrieve_filings(self, role: AgentRole, payload: RetrieveInput) -> RetrieveOutput:
        self.authorize(role, "retrieve_filings")
        started = time.perf_counter()
        try:
            hits = await self.retriever.search(
                payload.query,
                mode=payload.mode,
                top_k=payload.top_k,
                issuer_tickers=payload.issuer_tickers or None,
                document_types=payload.document_types or None,
                as_of=payload.as_of,
            )
        except Exception as exc:
            raise ToolFailureError("retrieve_filings failed", details={"error": str(exc)}) from exc
        latency_ms = int((time.perf_counter() - started) * 1000)
        return RetrieveOutput(hits=hits, latency_ms=latency_ms, empty=not hits)

    def yoy(self, role: AgentRole, payload: YoYInput) -> YoYOutput:
        self.authorize(role, "yoy")
        if payload.prior == 0:
            raise ToolFailureError("prior period value is zero")
        change = (payload.current - payload.prior) / abs(payload.prior) * 100.0
        direction = "up" if change > 0 else "down" if change < 0 else "flat"
        return YoYOutput(change_pct=round(change, 4), direction=direction)
