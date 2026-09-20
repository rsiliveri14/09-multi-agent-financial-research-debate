"""Optional Redis mirror of debate run status. Fail-open when Redis is down."""

from __future__ import annotations

from typing import Any

from observability.logging import get_logger

logger = get_logger(__name__)


class StatusCache:
    def __init__(self, url: str) -> None:
        self.url = url
        self._client: Any = None
        self.available = False

    async def connect(self) -> None:
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(self.url, decode_responses=True, socket_connect_timeout=0.4)
            await client.ping()
            self._client = client
            self.available = True
        except Exception:
            self.available = False
            self._client = None
            logger.info("redis_unavailable")

    async def set_status(self, request_id: str, status: str) -> None:
        if not self.available or self._client is None:
            return
        try:
            await self._client.set(f"debate:status:{request_id}", status, ex=3600)
        except Exception:
            self.available = False

    async def get_status(self, request_id: str) -> str | None:
        if not self.available or self._client is None:
            return None
        try:
            value = await self._client.get(f"debate:status:{request_id}")
            return str(value) if value else None
        except Exception:
            self.available = False
            return None
