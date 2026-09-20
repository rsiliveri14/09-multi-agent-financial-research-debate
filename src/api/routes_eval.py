from __future__ import annotations

from evaluation.runners.harness import run_suite
from fastapi import APIRouter, Depends, Request

from api.envelope import ok
from security.auth import require_roles
from services.runtime import get_runtime

router = APIRouter(prefix="/v1/eval", tags=["evaluation"])


@router.post("/run")
async def run_eval(request: Request, suite: str = "regression", _role: str = Depends(require_roles("admin"))):
    runtime = get_runtime()
    report = await run_suite(suite, runtime)
    runtime.last_eval = report
    await runtime.repository.save_eval(suite, report)
    return ok(getattr(request.state, "request_id", "req_eval"), report)


@router.get("/latest")
async def latest_eval(request: Request, _role: str = Depends(require_roles("analyst", "admin"))):
    runtime = get_runtime()
    report = runtime.last_eval or await runtime.repository.latest_eval() or {}
    return ok(getattr(request.state, "request_id", "req_eval"), report)
