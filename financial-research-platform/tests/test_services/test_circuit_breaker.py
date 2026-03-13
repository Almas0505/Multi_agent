"""Tests for circuit breaker behaviour in yfinance and news tools."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


def test_yfinance_breaker_falls_back_on_open_circuit():
    """When yfinance_breaker is OPEN, get_company_info should return mock data."""
    try:
        import pybreaker  # noqa: F401
    except ImportError:
        pytest.skip("pybreaker not installed")

    from app.tools.yfinance_tool import YFinanceTool

    tool = YFinanceTool()

    with patch("app.tools.yfinance_tool.yfinance_breaker") as mock_breaker:
        import pybreaker
        mock_breaker.call.side_effect = pybreaker.CircuitBreakerError("open")

        result = tool.get_company_info("AAPL")

    # Should return mock data, not raise
    assert isinstance(result, dict)
    assert "name" in result


def test_newsapi_breaker_falls_back_on_open_circuit():
    """When newsapi_breaker is OPEN, get_news should return mock data."""
    try:
        import pybreaker  # noqa: F401
    except ImportError:
        pytest.skip("pybreaker not installed")

    from app.tools.news_tool import NewsTool

    tool = NewsTool()

    with patch("app.tools.news_tool.newsapi_breaker") as mock_breaker, \
         patch("app.config.settings") as mock_settings:
        import pybreaker
        mock_settings.NEWS_API_KEY = "fake-key"
        mock_breaker.call.side_effect = pybreaker.CircuitBreakerError("open")

        result = tool.get_news("AAPL", "Apple Inc.")

    # Should fall back to mock news list
    assert isinstance(result, list)


def test_circuit_breaker_initialised():
    """Circuit breaker instances should be importable and have correct names."""
    from app.services.circuit_breaker import yfinance_breaker, newsapi_breaker, _PYBREAKER_AVAILABLE

    if not _PYBREAKER_AVAILABLE:
        pytest.skip("pybreaker not installed")

    assert yfinance_breaker.name == "yfinance"
    assert newsapi_breaker.name == "newsapi"


def test_noop_breaker_passthrough():
    """When pybreaker is absent the stub breaker calls the function directly."""
    from app.services.circuit_breaker import _NoOpBreaker  # type: ignore
    breaker = _NoOpBreaker()
    result = breaker.call(lambda: 42)
    assert result == 42
