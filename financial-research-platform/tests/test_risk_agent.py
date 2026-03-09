"""Tests for RiskAgent – mocks all external dependencies."""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.risk import RiskAgent
from app.models.state import FinancialResearchState


def _make_state(ticker: str = "AAPL") -> FinancialResearchState:
    return FinancialResearchState(
        ticker=ticker,
        company_name="Apple Inc.",
        sector="Technology",
        price_data=None,
        financial_statements=None,
        fundamentals_data=None,
        sentiment_data=None,
        technical_data=None,
        competitor_data=None,
        risk_data=None,
        final_analysis=None,
        pdf_path=None,
        report_id=None,
        errors=[],
        completed_agents=[],
        status="running",
        created_at="2024-01-01T00:00:00",
    )


def _make_price_data(n: int = 252) -> dict:
    """Deterministic price data."""
    closes = [round(150.0 + 10 * math.sin(i * 0.05), 4) for i in range(n)]
    return {
        "dates": [f"2023-01-{(i % 28) + 1:02d}" for i in range(n)],
        "open": [round(c * 0.99, 4) for c in closes],
        "high": [round(c * 1.01, 4) for c in closes],
        "low": [round(c * 0.98, 4) for c in closes],
        "close": closes,
        "volume": [50_000_000] * n,
    }


def _make_metrics() -> dict:
    return {
        "pe_ratio": 28.5,
        "pb_ratio": 50.0,
        "net_margin": 0.25,
        "roe": 1.47,
        "debt_equity": 1.8,
        "beta": 1.2,
        "free_cash_flow": 99_000_000_000,
        "revenue_growth": 0.08,
        "current_price": 175.0,
        "shares_outstanding": 15_550_000_000,
    }


# ---------------------------------------------------------------------------
# RiskAgent.run() returns correct structure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.agents.risk.YFinanceTool")
@patch("app.agents.risk.NewsTool")
async def test_risk_agent_run_returns_risk_data(mock_news_cls, mock_yf_cls) -> None:
    """RiskAgent.run() should return a dict with 'risk_data' key."""
    price_data = _make_price_data()

    mock_yf = mock_yf_cls.return_value
    mock_yf.get_historical_prices.return_value = price_data
    mock_yf.get_financial_metrics.return_value = _make_metrics()

    mock_news = mock_news_cls.return_value
    mock_news.get_news.return_value = []

    agent = RiskAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    assert "risk_data" in result
    rd = result["risk_data"]
    for key in ("beta", "var_95", "max_drawdown", "risk_level"):
        assert key in rd, f"Missing key: {key}"


@pytest.mark.asyncio
@patch("app.agents.risk.YFinanceTool")
@patch("app.agents.risk.NewsTool")
async def test_risk_agent_risk_level_is_valid(mock_news_cls, mock_yf_cls) -> None:
    """risk_level must be one of LOW / MEDIUM / HIGH."""
    price_data = _make_price_data()

    mock_yf = mock_yf_cls.return_value
    mock_yf.get_historical_prices.return_value = price_data
    mock_yf.get_financial_metrics.return_value = _make_metrics()

    mock_news = mock_news_cls.return_value
    mock_news.get_news.return_value = []

    agent = RiskAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    assert result["risk_data"]["risk_level"] in ("LOW", "MEDIUM", "HIGH")


@pytest.mark.asyncio
@patch("app.agents.risk.YFinanceTool")
@patch("app.agents.risk.NewsTool")
async def test_risk_agent_includes_volatility_and_sharpe(mock_news_cls, mock_yf_cls) -> None:
    """RiskAgent.run() should include volatility and sharpe_ratio in risk_data."""
    price_data = _make_price_data()

    mock_yf = mock_yf_cls.return_value
    mock_yf.get_historical_prices.return_value = price_data
    mock_yf.get_financial_metrics.return_value = _make_metrics()

    mock_news = mock_news_cls.return_value
    mock_news.get_news.return_value = []

    agent = RiskAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    rd = result["risk_data"]
    assert "volatility" in rd
    assert "sharpe_ratio" in rd


@pytest.mark.asyncio
@patch("app.agents.risk.YFinanceTool")
@patch("app.agents.risk.NewsTool")
async def test_risk_agent_appends_completed_agents(mock_news_cls, mock_yf_cls) -> None:
    """RiskAgent should add 'risk' to completed_agents."""
    price_data = _make_price_data()

    mock_yf = mock_yf_cls.return_value
    mock_yf.get_historical_prices.return_value = price_data
    mock_yf.get_financial_metrics.return_value = _make_metrics()

    mock_news = mock_news_cls.return_value
    mock_news.get_news.return_value = []

    agent = RiskAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    assert "risk" in result.get("completed_agents", [])


# ---------------------------------------------------------------------------
# Beta computation with known data
# ---------------------------------------------------------------------------


def test_beta_computation_with_known_data() -> None:
    """_calculate_beta_vs_spy should return a positive beta for correlated data."""
    import numpy as np

    agent = RiskAgent(llm=None)

    # Use random walk data where stock returns = 2 * spy returns + small noise
    rng = np.random.default_rng(42)
    n = 252
    spy_returns = rng.normal(0.0005, 0.01, n)
    # Stock returns are correlated with SPY: beta ≈ 2 (plus small noise)
    stock_returns = 2.0 * spy_returns + rng.normal(0, 0.001, n)

    # Convert returns to prices
    spy_closes = np.cumprod(1 + np.concatenate([[0], spy_returns])) * 100.0
    stock_closes = np.cumprod(1 + np.concatenate([[0], stock_returns])) * 100.0

    price_data = {"close": stock_closes.tolist(), "dates": [], "open": [], "high": [], "low": [], "volume": []}
    spy_data = {"close": spy_closes.tolist(), "dates": [], "open": [], "high": [], "low": [], "volume": []}

    beta = agent._calculate_beta_vs_spy(price_data, spy_data)
    # Beta should be approximately 2.0 for this correlated data
    assert 1.5 <= beta <= 2.5, f"Expected beta ~2.0, got {beta}"


def test_max_drawdown_correctness() -> None:
    """_calculate_max_drawdown should correctly compute peak-to-trough."""
    agent = RiskAgent(llm=None)

    # Price goes 100 -> 150 -> 75 (50% drawdown from peak)
    price_data = {"close": [100.0, 110.0, 120.0, 150.0, 130.0, 100.0, 75.0]}
    dd = agent._calculate_max_drawdown(price_data)
    # Peak = 150, trough = 75 → drawdown = (150-75)/150 = 0.5
    assert abs(dd - 0.5) < 0.01, f"Expected ~0.5 drawdown, got {dd}"
