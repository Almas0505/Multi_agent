"""Tests for TechnicalIndicatorsTool – mocks YFinanceTool to avoid network calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# compute_all
# ---------------------------------------------------------------------------


def _make_deterministic_price_data(n: int = 100) -> dict:
    """Return deterministic OHLCV data suitable for indicator computation."""
    import math
    base = 150.0
    closes = [round(base + 20 * math.sin(i * 0.1), 4) for i in range(n)]
    return {
        "dates": [f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n)],
        "open": [round(c * 0.99, 4) for c in closes],
        "high": [round(c * 1.01, 4) for c in closes],
        "low": [round(c * 0.98, 4) for c in closes],
        "close": closes,
        "volume": [50_000_000 + i * 1_000 for i in range(n)],
    }


@patch("app.tools.yfinance_tool.YFinanceTool")
def test_compute_all_returns_expected_keys(mock_yf_cls) -> None:
    """compute_all should return a dict with all required indicator keys."""
    from app.tools.technical_indicators import TechnicalIndicators

    mock_instance = MagicMock()
    mock_instance.get_historical_prices.return_value = _make_deterministic_price_data(100)
    mock_yf_cls.return_value = mock_instance

    tool = TechnicalIndicators()
    result = tool.compute_all("AAPL", period="1y")

    expected_keys = [
        "rsi", "macd", "bb_upper", "bb_lower", "sma20", "sma50",
        "support", "resistance", "current_price", "signal_line",
        "bb_middle", "volume_sma20",
    ]
    for key in expected_keys:
        assert key in result, f"Missing key in compute_all result: {key}"


@patch("app.tools.yfinance_tool.YFinanceTool")
def test_compute_all_rsi_in_valid_range(mock_yf_cls) -> None:
    """RSI returned by compute_all should be between 0 and 100."""
    from app.tools.technical_indicators import TechnicalIndicators

    mock_instance = MagicMock()
    mock_instance.get_historical_prices.return_value = _make_deterministic_price_data(100)
    mock_yf_cls.return_value = mock_instance

    tool = TechnicalIndicators()
    result = tool.compute_all("AAPL")

    rsi = result.get("rsi")
    if rsi is not None:
        assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"


@patch("app.tools.yfinance_tool.YFinanceTool")
def test_compute_all_support_below_resistance(mock_yf_cls) -> None:
    """Support level should be <= resistance level."""
    from app.tools.technical_indicators import TechnicalIndicators

    mock_instance = MagicMock()
    mock_instance.get_historical_prices.return_value = _make_deterministic_price_data(100)
    mock_yf_cls.return_value = mock_instance

    tool = TechnicalIndicators()
    result = tool.compute_all("AAPL")

    support = result.get("support")
    resistance = result.get("resistance")
    if support is not None and resistance is not None:
        assert support <= resistance, f"Support {support} > Resistance {resistance}"


# ---------------------------------------------------------------------------
# get_trend_signal
# ---------------------------------------------------------------------------


def test_get_trend_signal_bullish() -> None:
    """get_trend_signal returns BULLISH when all conditions met."""
    from app.tools.technical_indicators import TechnicalIndicators

    indicators = {
        "rsi": 60.0,
        "macd": 2.0,
        "signal_line": 1.0,
        "current_price": 180.0,
        "sma20": 175.0,
        "sma50": 165.0,
    }
    assert TechnicalIndicators.get_trend_signal(indicators) == "BULLISH"


def test_get_trend_signal_bearish() -> None:
    """get_trend_signal returns BEARISH when all bearish conditions met."""
    from app.tools.technical_indicators import TechnicalIndicators

    indicators = {
        "rsi": 40.0,
        "macd": -2.0,
        "signal_line": -1.0,
        "current_price": 140.0,
        "sma20": 150.0,
        "sma50": 160.0,
    }
    assert TechnicalIndicators.get_trend_signal(indicators) == "BEARISH"


def test_get_trend_signal_neutral() -> None:
    """get_trend_signal returns NEUTRAL for mixed signals."""
    from app.tools.technical_indicators import TechnicalIndicators

    indicators = {
        "rsi": 55.0,   # > 50 but MACD below signal
        "macd": 0.5,
        "signal_line": 1.0,
        "current_price": 180.0,
        "sma20": 175.0,
        "sma50": 165.0,
    }
    assert TechnicalIndicators.get_trend_signal(indicators) == "NEUTRAL"


def test_get_trend_signal_one_of_valid_values() -> None:
    """get_trend_signal always returns one of the three valid values."""
    from app.tools.technical_indicators import TechnicalIndicators

    for rsi in (30, 50, 70):
        for macd in (-1, 0, 1):
            result = TechnicalIndicators.get_trend_signal({
                "rsi": rsi, "macd": macd, "signal_line": 0,
                "current_price": 175, "sma20": 172, "sma50": 168,
            })
            assert result in ("BULLISH", "BEARISH", "NEUTRAL")


# ---------------------------------------------------------------------------
# generate_chart_from_indicators
# ---------------------------------------------------------------------------


def test_generate_chart_from_indicators_returns_string() -> None:
    """generate_chart_from_indicators should return a string (path or empty)."""
    from app.tools.technical_indicators import TechnicalIndicators

    tool = TechnicalIndicators()
    indicators = {
        "close": [150.0 + i * 0.1 for i in range(60)],
        "volume": [50_000_000] * 60,
        "dates": [f"2023-01-{(i % 28) + 1:02d}" for i in range(60)],
        "rsi": 55.0,
        "sma20": 155.0,
        "sma50": 152.0,
        "bb_upper": 165.0,
        "bb_middle": 155.0,
        "bb_lower": 145.0,
    }
    result = tool.generate_chart_from_indicators("AAPL", indicators)
    assert isinstance(result, str)
