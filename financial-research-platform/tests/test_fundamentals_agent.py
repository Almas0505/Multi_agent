"""Tests for FundamentalsAgent – mocks all external dependencies."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.agents.fundamentals import FundamentalsAgent
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


def _mock_metrics() -> dict:
    return {
        "pe_ratio": 25.5,
        "pb_ratio": 6.2,
        "ps_ratio": 7.1,
        "ev_ebitda": 18.3,
        "gross_margin": 0.43,
        "operating_margin": 0.28,
        "net_margin": 0.25,
        "roe": 0.35,
        "roa": 0.18,
        "debt_equity": 1.5,
        "current_ratio": 1.8,
        "quick_ratio": 1.4,
        "revenue_growth": 0.08,
        "earnings_growth": 0.12,
        "free_cash_flow": 90_000_000_000,
        "dividend_yield": 0.005,
        "beta": 1.2,
        "52w_high": 200.0,
        "52w_low": 130.0,
        "current_price": 175.0,
        "shares_outstanding": 15_550_000_000,
    }


# ---------------------------------------------------------------------------
# Basic structure tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fundamentals_agent_returns_expected_keys() -> None:
    """FundamentalsAgent.run() should always return the expected keys."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    assert "fundamentals_data" in result
    fd = result["fundamentals_data"]
    for key in ("pe_ratio", "pb_ratio", "net_margin", "roe", "dcf_fair_value", "rating"):
        assert key in fd, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_fundamentals_agent_rating_is_valid() -> None:
    """FundamentalsAgent should return a valid rating (BUY/HOLD/SELL)."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("MSFT"))
    rating = result["fundamentals_data"]["rating"]
    assert rating in ("BUY", "HOLD", "SELL"), f"Unexpected rating: {rating}"


@pytest.mark.asyncio
async def test_fundamentals_agent_appends_to_completed_agents() -> None:
    """FundamentalsAgent should add 'fundamentals' to completed_agents."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("TSLA"))
    assert "fundamentals" in result.get("completed_agents", [])


@pytest.mark.asyncio
async def test_fundamentals_agent_handles_invalid_ticker() -> None:
    """FundamentalsAgent should not raise on an unknown/invalid ticker."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("ZZZZZZ"))
    assert "fundamentals_data" in result


# ---------------------------------------------------------------------------
# Phase 2: new fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fundamentals_agent_returns_shares_outstanding() -> None:
    """Phase 2: fundamentals_data should include shares_outstanding."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))
    fd = result["fundamentals_data"]
    assert "shares_outstanding" in fd


@pytest.mark.asyncio
async def test_fundamentals_agent_returns_revenue_trend() -> None:
    """Phase 2: fundamentals_data should include revenue_trend."""
    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))
    fd = result["fundamentals_data"]
    assert "revenue_trend" in fd


# ---------------------------------------------------------------------------
# DCF computation
# ---------------------------------------------------------------------------


def test_dcf_computation_returns_positive_float() -> None:
    """_compute_dcf should return a positive float."""
    agent = FundamentalsAgent(llm=None)
    metrics = _mock_metrics()
    dcf = agent._compute_dcf(metrics, shares_outstanding=15_550_000_000)
    assert isinstance(dcf, float)
    assert dcf > 0, f"DCF value should be positive, got {dcf}"


def test_dcf_computation_with_real_shares() -> None:
    """_compute_dcf with a smaller share count should give a higher per-share value."""
    agent = FundamentalsAgent(llm=None)
    metrics = _mock_metrics()
    dcf_large = agent._compute_dcf(metrics, shares_outstanding=30_000_000_000)
    dcf_small = agent._compute_dcf(metrics, shares_outstanding=15_000_000_000)
    assert dcf_small > dcf_large, "Fewer shares => higher per-share DCF value"


# ---------------------------------------------------------------------------
# Mocked external calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("app.agents.fundamentals.YFinanceTool")
@patch("app.agents.fundamentals.SECEdgarTool")
async def test_fundamentals_agent_uses_real_shares(mock_sec_cls, mock_yf_cls) -> None:
    """FundamentalsAgent should call get_shares_outstanding and use it in DCF."""
    mock_yf = mock_yf_cls.return_value
    mock_yf.get_financial_metrics.return_value = _mock_metrics()
    mock_yf.get_shares_outstanding.return_value = 15_550_000_000
    mock_yf.get_income_statement_summary.return_value = {
        "revenue": {"2023-09-30": 383_285_000_000},
        "net_income": {},
        "gross_profit": {},
        "operating_income": {},
    }

    mock_sec = mock_sec_cls.return_value
    mock_sec.get_annual_report_summary.return_value = {
        "cik": "N/A",
        "company_name": "Apple Inc.",
        "last_10k_date": "2023-09-30",
        "last_10k_accession": "N/A",
        "summary_text": "Mock SEC summary.",
    }

    agent = FundamentalsAgent(llm=None)
    result = await agent.run(_make_state("AAPL"))

    assert "fundamentals_data" in result
    # Should have called get_shares_outstanding
    mock_yf.get_shares_outstanding.assert_called_once_with("AAPL")
