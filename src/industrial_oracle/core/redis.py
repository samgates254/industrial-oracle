"""Redis integration client with in-memory fallback for local and test runs."""

import asyncio
from typing import Any, Dict, Optional
import logging

from industrial_oracle.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryRedisClient:
    """In-memory Redis implementation for development and testing environments."""

    def __init__(self) -> None:
        self._data: Dict[str, str] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            return self._data.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        async with self._lock:
            self._data[key] = str(value)
            return True

    async def setex(self, key: str, time: int, value: Any) -> bool:
        return await self.set(key, value, ex=time)

    async def delete(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for k in keys:
                if k in self._data:
                    del self._data[k]
                    count += 1
            return count

    async def exists(self, *keys: str) -> int:
        async with self._lock:
            return sum(1 for k in keys if k in self._data)

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        pass


class RedisManager:
    """Manages Redis connection lifecycle and client instantiation."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._client: Optional[Any] = None

    async def initialize(self) -> None:
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(self.url, decode_responses=True)
            await client.ping()
            self._client = client
            logger.info("Connected to Redis at %s", self.url)
        except Exception as exc:
            logger.warning("Native Redis connection unavailable (%s); using in-memory Redis client.", exc)
            self._client = InMemoryRedisClient()

    async def get_client(self) -> Any:
        if self._client is None:
            await self.initialize()
        return self._client

    async def close(self) -> None:
        if self._client and hasattr(self._client, "close"):
            await self._client.close()


redis_manager = RedisManager(settings.REDIS_URL)


async def get_redis_client() -> Any:
    """Dependency provider for Redis client."""
    return await redis_manager.get_client()
