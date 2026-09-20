from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from config.settings import reset_settings_cache
from services.runtime import build_runtime, get_runtime, set_runtime

collect_ignore = ["load/locustfile.py"]


@pytest.fixture(autouse=True)
def _reset_settings(monkeypatch):
    monkeypatch.setenv("STORE_BACKEND", "memory")
    monkeypatch.setenv("LLM_PROVIDER", "heuristic")
    reset_settings_cache()
    yield
    try:
        runtime = get_runtime()
        runtime.failure_flags.clear()
        runtime.orchestrator.failure_flags = runtime.failure_flags
    except RuntimeError:
        pass


@pytest.fixture(scope="session")
async def runtime():
    instance = await build_runtime()
    set_runtime(instance)
    return instance


@pytest.fixture
async def client(runtime):
    from api.main import create_app

    set_runtime(runtime)
    app = create_app()
    app.state.runtime = runtime
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


def auth(role: str = "analyst") -> dict[str, str]:
    token = "dev-analyst-token" if role == "analyst" else "dev-admin-token"
    return {"Authorization": f"Bearer {token}"}
