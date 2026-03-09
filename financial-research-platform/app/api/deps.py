"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.services.cache import CacheService

# Singleton cache instance reused across requests
_cache_service = CacheService()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for use as a FastAPI dependency."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_cache() -> CacheService:
    """Return the shared CacheService instance."""
    return _cache_service
