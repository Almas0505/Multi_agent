"""Tests for the WebSocket progress streaming endpoint."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_websocket_returns_waiting_when_no_progress():
    """WebSocket sends a 'waiting' message when no progress is cached."""
    client = TestClient(app)

    with patch("app.api.routes.websocket.CacheService") as MockCache:
        instance = MockCache.return_value
        # Return empty dict (no progress), then raise disconnect to end loop
        instance.get_progress = AsyncMock(side_effect=[{}, Exception("disconnect")])

        with client.websocket_connect("/ws/analysis/unknown-task-id") as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["status"] == "waiting"
            assert msg["progress"] == 0


def test_websocket_closes_on_completed():
    """WebSocket closes when the task status reaches 'completed'."""
    client = TestClient(app)

    completed_progress = {
        "agent": "complete",
        "status": "completed",
        "progress": 100,
        "message": "Analysis complete.",
    }

    with patch("app.api.routes.websocket.CacheService") as MockCache:
        instance = MockCache.return_value
        instance.get_progress = AsyncMock(return_value=completed_progress)

        with client.websocket_connect("/ws/analysis/some-task-id") as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["status"] == "completed"
            assert msg["progress"] == 100


def test_websocket_message_has_required_fields():
    """Each WebSocket message contains agent, status, progress, message fields."""
    client = TestClient(app)

    progress = {
        "agent": "fundamentals",
        "status": "running",
        "progress": 30,
        "message": "Running fundamentals…",
    }

    with patch("app.api.routes.websocket.CacheService") as MockCache:
        instance = MockCache.return_value
        # Return running once, then completed to close
        completed = {"agent": "complete", "status": "completed", "progress": 100, "message": "Done"}
        instance.get_progress = AsyncMock(side_effect=[progress, completed])

        with client.websocket_connect("/ws/analysis/task-123") as ws:
            msg = json.loads(ws.receive_text())
            assert "agent" in msg
            assert "status" in msg
            assert "progress" in msg
            assert "message" in msg
