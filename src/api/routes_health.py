from __future__ import annotations

from fastapi import APIRouter, Response

from observability.metrics import metrics_payload
from services.runtime import get_runtime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    runtime = get_runtime()
    if not runtime.ready or not runtime.chunks:
        response.status_code = 503
        return {"status": "not_ready"}
    return {
        "status": "ready",
        "chunks": len(runtime.chunks),
        "store": runtime.settings.store_backend,
        "redis": bool(runtime.status_cache and runtime.status_cache.available),
    }


@router.get("/metrics")
async def metrics() -> Response:
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)
