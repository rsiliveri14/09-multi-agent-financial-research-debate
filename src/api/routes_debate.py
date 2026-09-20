from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from api.envelope import fail, ok
from domain.errors import DatabaseFailureError
from domain.models import DebateRequest
from security.auth import require_roles
from services.debate import to_run_record
from services.runtime import get_runtime

router = APIRouter(prefix="/v1", tags=["debate"])


@router.post("/debate")
async def create_debate(
    payload: DebateRequest, request: Request, _role: str = Depends(require_roles("analyst", "admin"))
):
    runtime = get_runtime()
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    if runtime.failure_flags.get("database_failure"):
        raise DatabaseFailureError()
    result = await runtime.orchestrator.run(payload, request_id=request_id)
    record = to_run_record(result)
    await runtime.repository.save(record)
    if runtime.status_cache is not None:
        await runtime.status_cache.set_status(request_id, result.status.value)
    return ok(request_id, result.model_dump(mode="json"), status=result.status.value)


@router.get("/debate/{request_id}")
async def get_debate(request_id: str, request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    record = await runtime.repository.get(request_id)
    if record is None or record.result is None:
        return fail(getattr(request.state, "request_id", request_id), "NOT_FOUND", "run not found")
    return ok(request_id, record.result.model_dump(mode="json"), status=record.status.value)


@router.get("/debate/{request_id}/trace")
async def get_trace(request_id: str, request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    record = await runtime.repository.get(request_id)
    if record is None:
        return fail(getattr(request.state, "request_id", request_id), "NOT_FOUND", "run not found")
    events = [event.model_dump(mode="json") for event in record.events]
    return ok(request_id, {"events": events, "terminal_state": record.terminal_state}, status=record.status.value)


@router.get("/debate/{request_id}/graph")
async def get_graph(request_id: str, request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    record = await runtime.repository.get(request_id)
    if record is None or record.result is None:
        return fail(getattr(request.state, "request_id", request_id), "NOT_FOUND", "run not found")
    return ok(request_id, record.result.graph.model_dump(mode="json"), status=record.status.value)


@router.get("/debates")
async def list_debates(request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    records = await runtime.repository.list(limit=40)
    items = [
        {
            "request_id": record.request_id,
            "question": record.question,
            "status": record.status.value,
            "terminal_state": record.terminal_state.value,
            "latency_ms": record.latency_ms,
            "estimated_cost_usd": record.estimated_cost_usd,
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]
    return ok(getattr(request.state, "request_id", "req_list"), {"items": items})


@router.get("/corpus")
async def corpus_summary(request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    tickers: dict[str, int] = {}
    for chunk in runtime.chunks:
        tickers[chunk.issuer_ticker] = tickers.get(chunk.issuer_ticker, 0) + 1
    return ok(
        getattr(request.state, "request_id", "req_corpus"),
        {"chunks": len(runtime.chunks), "tickers": tickers},
    )
