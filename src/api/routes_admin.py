from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.envelope import ok
from security.auth import require_roles
from services.runtime import get_runtime

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/simulate-failure")
async def simulate_failure(payload: dict[str, bool], request: Request, _role: str = Depends(require_roles("admin"))):
    runtime = get_runtime()
    allowed = {
        "provider_timeout",
        "tool_timeout",
        "empty_retrieval",
        "invalid_structured_output",
        "database_failure",
    }
    runtime.failure_flags.clear()
    for key, value in payload.items():
        if key in allowed:
            runtime.failure_flags[key] = bool(value)
    runtime.orchestrator.failure_flags = runtime.failure_flags
    return ok(getattr(request.state, "request_id", "req_admin"), {"flags": runtime.failure_flags})


@router.get("/nodes")
async def node_catalog(request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    from agents.registry import NODE_CATALOG

    return ok(getattr(request.state, "request_id", "req_nodes"), NODE_CATALOG)
