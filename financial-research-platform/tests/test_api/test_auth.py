"""Tests for API key authentication middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client_with_auth():
    """Client against an app instance with AUTH_ENABLED=True and a fixed API key."""
    from app.config import settings

    original_auth = settings.AUTH_ENABLED
    original_key = settings.API_KEY
    settings.AUTH_ENABLED = True
    settings.API_KEY = "test-secret-key"

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    settings.AUTH_ENABLED = original_auth
    settings.API_KEY = original_key


@pytest.mark.asyncio
async def test_health_no_auth_required(client_with_auth):
    """Health endpoint must not require authentication."""
    resp = await client_with_auth.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(client_with_auth):
    """Requests without X-API-Key return 401 when AUTH_ENABLED."""
    resp = await client_with_auth.get("/api/v1/reports/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_api_key_returns_401(client_with_auth):
    """Requests with the wrong key return 401."""
    resp = await client_with_auth.get(
        "/api/v1/reports/", headers={"X-API-Key": "wrong-key"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_correct_api_key_passes(client_with_auth):
    """Requests with the correct key are allowed through (DB may be absent → any non-401 status)."""
    from unittest.mock import AsyncMock, patch

    with patch("app.api.routes.reports.crud.get_reports", new_callable=AsyncMock, return_value=[]):
        resp = await client_with_auth.get(
            "/api/v1/reports/", headers={"X-API-Key": "test-secret-key"}
        )
    # Auth passed – any status other than 401 is acceptable
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_auth_disabled_allows_all(client):
    """When AUTH_ENABLED=False (default), all requests pass without a key."""
    from unittest.mock import AsyncMock, patch

    with patch("app.api.routes.reports.crud.get_reports", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/v1/reports/")
    assert resp.status_code != 401
