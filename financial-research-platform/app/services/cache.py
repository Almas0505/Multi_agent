"""Redis-backed cache service."""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

try:
    import redis.asyncio as aioredis  # type: ignore
    _REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REDIS_AVAILABLE = False

from app.config import settings


class CacheService:
    """Async cache service backed by Redis with an in-memory fallback."""

    def __init__(self) -> None:
        self._redis = None
        self._fallback: dict[str, Any] = {}

    async def _get_client(self):
        if not _REDIS_AVAILABLE:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._redis.ping()
            except Exception as exc:
                logger.warning(f"Redis connection failed: {exc}. Using in-memory fallback.")
                self._redis = None
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by *key*; returns None if not found."""
        client = await self._get_client()
        if client is None:
            return self._fallback.get(key)
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            logger.warning(f"Cache get failed for {key}: {exc}")
            return self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store *value* at *key* with optional TTL in seconds."""
        client = await self._get_client()
        serialised = json.dumps(value)
        if client is None:
            self._fallback[key] = value
            return
        try:
            await client.set(key, serialised, ex=ttl)
        except Exception as exc:
            logger.warning(f"Cache set failed for {key}: {exc}")
            self._fallback[key] = value

    async def delete(self, key: str) -> None:
        """Remove *key* from the cache."""
        client = await self._get_client()
        if client is None:
            self._fallback.pop(key, None)
            return
        try:
            await client.delete(key)
        except Exception as exc:
            logger.warning(f"Cache delete failed for {key}: {exc}")
            self._fallback.pop(key, None)

    async def get_progress(self, task_id: str) -> dict:
        """Return the progress dict for *task_id*."""
        return await self.get(f"progress:{task_id}") or {}

    async def set_progress(self, task_id: str, progress: dict) -> None:
        """Persist a progress dict for *task_id* (TTL 24 h)."""
        await self.set(f"progress:{task_id}", progress, ttl=86400)
