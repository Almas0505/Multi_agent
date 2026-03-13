"""Tests for the unified error schema."""

from __future__ import annotations

import pytest
from app.models.errors import ErrorDetail, make_agent_error


def test_error_detail_has_required_fields():
    err = ErrorDetail(code="AGENT_ERROR", message="something failed", agent="fundamentals")
    assert err.code == "AGENT_ERROR"
    assert err.message == "something failed"
    assert err.agent == "fundamentals"
    assert err.timestamp  # auto-populated


def test_error_detail_agent_optional():
    err = ErrorDetail(code="VALIDATION_ERROR", message="bad input")
    assert err.agent is None


def test_make_agent_error_returns_dict():
    result = make_agent_error("risk", ValueError("bad value"))
    assert isinstance(result, dict)
    assert result["code"] == "AGENT_ERROR"
    assert result["agent"] == "risk"
    assert "bad value" in result["message"]


def test_make_agent_error_timestamp_present():
    result = make_agent_error("sentiment", RuntimeError("fail"))
    assert "timestamp" in result
    assert result["timestamp"]  # non-empty string
