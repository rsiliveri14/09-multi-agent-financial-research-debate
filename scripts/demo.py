"""Run a scripted debate used in the portfolio demo."""

from __future__ import annotations

import asyncio
import json

from domain.models import DebateRequest
from services.runtime import build_runtime


async def main() -> None:
    runtime = await build_runtime()
    request = DebateRequest(question="Apple Q2 FY2025 net sales: reconcile the 8-K preliminary figure versus the 10-Q.")
    result = await runtime.orchestrator.run(request, request_id="demo_aapl_q2")
    print(
        json.dumps(
            {
                "request_id": result.request_id,
                "terminal_state": result.terminal_state,
                "headline": result.synthesis.headline,
                "contradictions": result.metrics.contradiction_count,
                "unresolved": result.synthesis.unresolved,
                "latency_ms": result.metrics.latency_ms,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
