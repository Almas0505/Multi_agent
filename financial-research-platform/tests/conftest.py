"""Pytest fixtures shared across the test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.state import FinancialResearchState


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app (no live server)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Phase 2 shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_yfinance_data() -> dict:
    """Deterministic mock yfinance OHLCV price data (252 trading days)."""
    import math
    n = 252
    base = 150.0
    # Simple sinusoidal price movement for deterministic tests
    closes = [round(base + 20 * math.sin(i * 0.05), 2) for i in range(n)]
    return {
        "dates": [f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n)],
        "open": [round(c * 0.99, 2) for c in closes],
        "high": [round(c * 1.01, 2) for c in closes],
        "low": [round(c * 0.98, 2) for c in closes],
        "close": closes,
        "volume": [50_000_000 + i * 10_000 for i in range(n)],
    }


@pytest.fixture
def mock_llm():
    """Mock LangChain-compatible LLM that returns a fixed analysis string."""
    llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Mock LLM analysis: BUY rating based on strong fundamentals."
    llm.ainvoke = AsyncMock(return_value=mock_response)
    return llm


@pytest.fixture
def sample_state() -> FinancialResearchState:
    """Sample FinancialResearchState with ticker='AAPL'."""
    return FinancialResearchState(
        ticker="AAPL",
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
