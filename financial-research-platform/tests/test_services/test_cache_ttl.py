"""Tests for configurable cache TTL behaviour."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_set_uses_analysis_ttl_by_default():
    """CacheService.set() without explicit ttl uses settings.CACHE_TTL_ANALYSIS."""
    from app.services.cache import CacheService
    from app.config import settings

    cache = CacheService()
    mock_client = AsyncMock()
    cache._redis = mock_client
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.set = AsyncMock()

    with patch.object(cache, "_get_client", return_value=mock_client):
        await cache.set("test-key", {"value": 1})

    mock_client.set.assert_called_once()
    _, kwargs = mock_client.set.call_args
    assert kwargs.get("ex") == settings.CACHE_TTL_ANALYSIS


@pytest.mark.asyncio
async def test_set_progress_uses_progress_ttl():
    """CacheService.set_progress() uses settings.CACHE_TTL_PROGRESS."""
    from app.services.cache import CacheService
    from app.config import settings

    cache = CacheService()
    mock_client = AsyncMock()
    cache._redis = mock_client
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.set = AsyncMock()

    with patch.object(cache, "_get_client", return_value=mock_client):
        await cache.set_progress("task-123", {"progress": 50, "status": "running"})

    mock_client.set.assert_called_once()
    _, kwargs = mock_client.set.call_args
    assert kwargs.get("ex") == settings.CACHE_TTL_PROGRESS


@pytest.mark.asyncio
async def test_set_with_explicit_ttl_overrides_default():
    """Explicit ttl parameter takes precedence over settings default."""
    from app.services.cache import CacheService

    cache = CacheService()
    mock_client = AsyncMock()
    cache._redis = mock_client
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.set = AsyncMock()

    with patch.object(cache, "_get_client", return_value=mock_client):
        await cache.set("news-key", {"articles": []}, ttl=1800)

    _, kwargs = mock_client.set.call_args
    assert kwargs.get("ex") == 1800
