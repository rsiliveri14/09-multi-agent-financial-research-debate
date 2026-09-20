from domain.enums import RunStatus, TerminalState
from domain.models import DebateRunRecord
from repositories.memory import MemoryRunRepository
from services.cache import StatusCache


async def test_status_cache_fail_open_without_redis():
    cache = StatusCache("redis://127.0.0.1:1/0")
    await cache.connect()
    assert cache.available is False
    await cache.set_status("req_x", "completed")
    assert await cache.get_status("req_x") is None


async def test_memory_eval_roundtrip():
    repo = MemoryRunRepository()
    record = DebateRunRecord(
        request_id="req_mem",
        question="q",
        status=RunStatus.COMPLETED,
        terminal_state=TerminalState.COMPLETED,
    )
    await repo.save(record)
    loaded = await repo.get("req_mem")
    assert loaded is not None
    await repo.save_eval("regression", {"n": 6, "suite": "regression"})
    latest = await repo.latest_eval()
    assert latest is not None
    assert latest["n"] == 6
