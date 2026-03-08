"""Tests for the analysis API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """GET /health should return 200 with status 'ok'."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_analyze_valid_ticker(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/v1/analyze/AAPL should return 200 with a task_id."""
    # Patch crud.create_report to avoid needing a live DB
    import uuid
    from unittest.mock import AsyncMock, MagicMock

    mock_report = MagicMock()
    mock_report.id = uuid.uuid4()

    monkeypatch.setattr("app.db.crud.create_report", AsyncMock(return_value=mock_report))
    monkeypatch.setattr("app.services.cache.CacheService.set_progress", AsyncMock())
    monkeypatch.setattr("app.services.cache.CacheService.get", AsyncMock(return_value=None))

    # Prevent real Celery dispatch
    try:
        import app.services.celery_app as celery_module
        if celery_module._CELERY_AVAILABLE:
            monkeypatch.setattr(
                celery_module.run_financial_analysis,
                "delay",
                MagicMock(),
            )
    except Exception:
        pass

    response = await client.post("/api/v1/analyze/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] in ("queued", "completed")


@pytest.mark.asyncio
async def test_analyze_invalid_ticker(client: AsyncClient) -> None:
    """POST /api/v1/analyze/INVALID123456 should return 422 for an oversized ticker."""
    response = await client.post("/api/v1/analyze/INVALID123456")
    assert response.status_code == 422
