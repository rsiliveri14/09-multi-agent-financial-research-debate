import os

import pytest

from config.settings import Settings
from db.session import create_all, create_engine, session_factory
from domain.enums import RunStatus, TerminalState
from domain.models import DebateRunRecord, RunEvent
from repositories.postgres import PostgresRunRepository
from services.cache import StatusCache


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("INTEGRATION") != "1", reason="requires postgres")
async def test_postgres_roundtrip():
    settings = Settings(
        store_backend="postgres",
        database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://debate:debate@localhost:5439/debate"),
    )
    engine = create_engine(settings)
    await create_all(engine)
    repo = PostgresRunRepository(session_factory(engine))
    record = DebateRunRecord(
        request_id="req_integration",
        question="integration",
        status=RunStatus.COMPLETED,
        terminal_state=TerminalState.COMPLETED,
        events=[
            RunEvent(seq=1, event_type="plan.completed", node="plan", payload={"ok": True}),
        ],
    )
    await repo.save(record)
    loaded = await repo.get("req_integration")
    assert loaded is not None
    assert loaded.question == "integration"
    assert loaded.events[0].node == "plan"
    listed = await repo.list(limit=10)
    assert any(item.request_id == "req_integration" for item in listed)
    await repo.save_eval("regression", {"n": 6, "suite": "regression"})
    latest = await repo.latest_eval()
    assert latest is not None
    assert latest["n"] == 6
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("INTEGRATION") != "1", reason="requires redis")
async def test_redis_status_cache():
    cache = StatusCache(os.getenv("REDIS_URL", "redis://localhost:6389/0"))
    await cache.connect()
    assert cache.available is True
    await cache.set_status("req_integration_cache", "completed")
    assert await cache.get_status("req_integration_cache") == "completed"
