"""Tests for the FundamentalsAgent."""

from __future__ import annotations

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
    # Should fall back to mock data without raising
    assert "fundamentals_data" in result
