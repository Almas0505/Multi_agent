"""Tests for YFinanceTool – no real network calls (yfinance is mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.tools.yfinance_tool import YFinanceTool


def _make_mock_ticker(info: dict | None = None, financials=None, balance_sheet=None, cashflow=None):
    """Build a minimal mock yfinance.Ticker object."""
    import pandas as pd

    mock_ticker = MagicMock()
    mock_ticker.info = info or {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "United States",
        "website": "https://www.apple.com",
        "longBusinessSummary": "Apple designs consumer electronics.",
        "fullTimeEmployees": 164000,
        "marketCap": 3_000_000_000_000,
        "currency": "USD",
        "trailingPE": 28.5,
        "priceToBook": 50.0,
        "priceToSalesTrailing12Months": 7.5,
        "enterpriseToEbitda": 22.0,
        "grossMargins": 0.44,
        "operatingMargins": 0.30,
        "profitMargins": 0.25,
        "returnOnEquity": 1.47,
        "returnOnAssets": 0.28,
        "debtToEquity": 1.8,
        "currentRatio": 0.94,
        "quickRatio": 0.90,
        "revenueGrowth": 0.08,
        "earningsGrowth": 0.12,
        "freeCashflow": 99_000_000_000,
        "dividendYield": 0.005,
        "beta": 1.2,
        "fiftyTwoWeekHigh": 200.0,
        "fiftyTwoWeekLow": 130.0,
        "currentPrice": 175.0,
        "sharesOutstanding": 15_550_000_000,
    }

    # Build a minimal DataFrame for financials
    if financials is None:
        financials = pd.DataFrame(
            {
                pd.Timestamp("2023-09-30"): {"Total Revenue": 383_285_000_000, "Net Income": 96_995_000_000, "Gross Profit": 169_148_000_000, "Operating Income": 114_301_000_000},
                pd.Timestamp("2022-09-30"): {"Total Revenue": 394_328_000_000, "Net Income": 99_803_000_000, "Gross Profit": 170_782_000_000, "Operating Income": 119_437_000_000},
            }
        )
    mock_ticker.financials = financials

    if balance_sheet is None:
        balance_sheet = pd.DataFrame(
            {
                pd.Timestamp("2023-09-30"): {"Total Assets": 352_583_000_000, "Total Debt": 109_280_000_000, "Stockholders Equity": 62_146_000_000, "Cash And Cash Equivalents": 29_965_000_000},
                pd.Timestamp("2022-09-30"): {"Total Assets": 352_755_000_000, "Total Debt": 120_069_000_000, "Stockholders Equity": 50_672_000_000, "Cash And Cash Equivalents": 23_646_000_000},
            }
        )
    mock_ticker.balance_sheet = balance_sheet

    if cashflow is None:
        cashflow = pd.DataFrame(
            {
                pd.Timestamp("2023-09-30"): {"Operating Cash Flow": 110_543_000_000, "Free Cash Flow": 99_584_000_000, "Capital Expenditure": -10_959_000_000},
                pd.Timestamp("2022-09-30"): {"Operating Cash Flow": 122_151_000_000, "Free Cash Flow": 111_443_000_000, "Capital Expenditure": -10_708_000_000},
            }
        )
    mock_ticker.cashflow = cashflow

    return mock_ticker


# --------------------------------------------------------------------------
# get_financial_metrics
# --------------------------------------------------------------------------


@patch("app.tools.yfinance_tool.yf")
def test_get_financial_metrics_returns_expected_keys(mock_yf) -> None:
    """get_financial_metrics should return a dict with all required keys."""
    mock_yf.Ticker.return_value = _make_mock_ticker()

    tool = YFinanceTool()
    result = tool.get_financial_metrics("AAPL")

    expected_keys = [
        "pe_ratio", "pb_ratio", "ps_ratio", "ev_ebitda",
        "gross_margin", "operating_margin", "net_margin",
        "roe", "roa", "debt_equity", "current_ratio", "quick_ratio",
        "revenue_growth", "earnings_growth", "free_cash_flow",
        "dividend_yield", "beta", "52w_high", "52w_low", "current_price",
        "shares_outstanding",
    ]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"


# --------------------------------------------------------------------------
# get_historical_prices
# --------------------------------------------------------------------------


@patch("app.tools.yfinance_tool.yf")
def test_get_historical_prices_returns_expected_structure(mock_yf) -> None:
    """get_historical_prices should return a dict with OHLCV lists."""
    import pandas as pd

    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    mock_hist = pd.DataFrame(
        {
            "Open": [150.0 + i for i in range(10)],
            "High": [152.0 + i for i in range(10)],
            "Low": [148.0 + i for i in range(10)],
            "Close": [151.0 + i for i in range(10)],
            "Volume": [50_000_000] * 10,
        },
        index=dates,
    )
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_hist
    mock_yf.Ticker.return_value = mock_ticker

    tool = YFinanceTool()
    result = tool.get_historical_prices("AAPL", period="1mo")

    for key in ("dates", "open", "high", "low", "close", "volume"):
        assert key in result, f"Missing key: {key}"
    assert len(result["close"]) == 10


# --------------------------------------------------------------------------
# get_peer_companies
# --------------------------------------------------------------------------


def test_get_peer_companies_aapl_contains_msft() -> None:
    """get_peer_companies('AAPL') should include MSFT."""
    tool = YFinanceTool()
    peers = tool.get_peer_companies("AAPL")
    assert "MSFT" in peers


def test_get_peer_companies_unknown_ticker_returns_default() -> None:
    """get_peer_companies with an unknown ticker returns a default list."""
    tool = YFinanceTool()
    peers = tool.get_peer_companies("ZZZZZZ")
    assert isinstance(peers, list)
    assert len(peers) > 0


# --------------------------------------------------------------------------
# get_shares_outstanding
# --------------------------------------------------------------------------


@patch("app.tools.yfinance_tool.yf")
def test_get_shares_outstanding_returns_positive_number(mock_yf) -> None:
    """get_shares_outstanding should return a positive integer."""
    mock_yf.Ticker.return_value = _make_mock_ticker()

    tool = YFinanceTool()
    shares = tool.get_shares_outstanding("AAPL")

    assert isinstance(shares, (int, float))
    assert shares > 0


@patch("app.tools.yfinance_tool._YFINANCE_AVAILABLE", False)
def test_get_shares_outstanding_fallback() -> None:
    """get_shares_outstanding returns fallback when yfinance unavailable."""
    tool = YFinanceTool()
    shares = tool.get_shares_outstanding("AAPL")
    assert shares == 15_000_000_000


# --------------------------------------------------------------------------
# get_income_statement_summary
# --------------------------------------------------------------------------


@patch("app.tools.yfinance_tool.yf")
def test_get_income_statement_summary_returns_expected_keys(mock_yf) -> None:
    """get_income_statement_summary should return dict with revenue, net_income, etc."""
    mock_yf.Ticker.return_value = _make_mock_ticker()

    tool = YFinanceTool()
    result = tool.get_income_statement_summary("AAPL")

    for key in ("revenue", "net_income", "gross_profit", "operating_income"):
        assert key in result, f"Missing key: {key}"
