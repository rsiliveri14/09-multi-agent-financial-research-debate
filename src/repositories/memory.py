from __future__ import annotations

from typing import Any

from domain.models import DebateRunRecord
from repositories.protocol import RunRepository


class MemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._items: dict[str, DebateRunRecord] = {}
        self._order: list[str] = []
        self._evals: list[dict[str, Any]] = []

    async def save(self, record: DebateRunRecord) -> DebateRunRecord:
        self._items[record.request_id] = record
        if record.request_id not in self._order:
            self._order.append(record.request_id)
        return record

    async def get(self, request_id: str) -> DebateRunRecord | None:
        return self._items.get(request_id)

    async def list(self, limit: int = 50) -> list[DebateRunRecord]:
        ids = list(reversed(self._order))[:limit]
        return [self._items[item] for item in ids if item in self._items]

    async def save_eval(self, suite: str, report: dict[str, Any]) -> None:
        self._evals.append({"suite": suite, **report})

    async def latest_eval(self) -> dict[str, Any] | None:
        return self._evals[-1] if self._evals else None
