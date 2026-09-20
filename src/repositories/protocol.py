from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.models import DebateRunRecord


class RunRepository(ABC):
    @abstractmethod
    async def save(self, record: DebateRunRecord) -> DebateRunRecord:
        raise NotImplementedError

    @abstractmethod
    async def get(self, request_id: str) -> DebateRunRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, limit: int = 50) -> list[DebateRunRecord]:
        raise NotImplementedError

    @abstractmethod
    async def save_eval(self, suite: str, report: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def latest_eval(self) -> dict[str, Any] | None:
        raise NotImplementedError
