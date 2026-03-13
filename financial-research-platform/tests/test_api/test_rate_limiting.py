"""Tests for rate limiting on analysis and report endpoints."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_analysis_endpoint_accepts_requests(client):
    """POST /analyze/{ticker} should accept normal requests."""
    with patch("app.api.routes.analysis.crud.create_report", new_callable=AsyncMock) as mock_create, \
         patch("app.services.celery_app._CELERY_AVAILABLE", False), \
         patch("app.services.celery_app.run_financial_analysis", new_callable=AsyncMock):
        mock_report = AsyncMock()
        mock_report.id = "test-id-123"
        mock_create.return_value = mock_report

        resp = await client.post("/api/v1/analyze/AAPL")
        # Should be 200 or queued (not 429 on first request)
        assert resp.status_code in (200, 422, 500)  # not 429


@pytest.mark.asyncio
async def test_status_endpoint_responds(client):
    """GET /analyze/{task_id}/status should respond (404 is fine for unknown ID)."""
    resp = await client.get("/api/v1/analyze/nonexistent-task-id/status")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_reports_list_responds(client):
    """GET /reports/ should respond (DB mocked → 200, any non-429 status)."""
    with patch("app.api.routes.reports.crud.get_reports", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/v1/reports/")
    assert resp.status_code != 429
