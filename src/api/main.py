from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.errors import install_error_handlers
from api.routes_admin import router as admin_router
from api.routes_debate import router as debate_router
from api.routes_eval import router as eval_router
from api.routes_health import router as health_router
from config.settings import get_settings
from services.runtime import build_runtime, set_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    runtime = await build_runtime(settings)
    set_runtime(runtime)
    app.state.runtime = runtime
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Multi-Agent Financial Research Debate",
        version="0.1.0",
        description="Evidence-driven debate among Bull, Bear, Financial, Risk, and Evidence specialists.",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Liveness, readiness, Prometheus metrics."},
            {"name": "debate", "description": "Run a debate, fetch traces, graphs, and corpus summary."},
            {"name": "evaluation", "description": "Regression / full suite vs single-agent RAG."},
            {"name": "admin", "description": "Failure injection and node catalog."},
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(debate_router)
    app.include_router(admin_router)
    app.include_router(eval_router)
    return app


app = create_app()
