"""LangGraph orchestrator that wires all agents into a StateGraph."""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.models.state import FinancialResearchState

try:
    from langgraph.graph import END, StateGraph  # type: ignore
    _LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LANGGRAPH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Progress helper
# ---------------------------------------------------------------------------

async def _emit_progress(report_id: str | None, agent: str, progress: int, message: str) -> None:
    """Write a progress update to the cache. Silently skips if report_id is absent."""
    if not report_id:
        return
    try:
        from app.services.cache import CacheService
        cache = CacheService()
        await cache.set_progress(
            report_id,
            {"agent": agent, "progress": progress, "status": "running", "message": message},
        )
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Progress update failed for {report_id}: {exc}")


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

async def init_node(state: FinancialResearchState) -> dict:
    """Validate ticker and initialise workflow state."""
    ticker = state.get("ticker", "").strip().upper()
    if not ticker or len(ticker) > 10:
        raise ValueError(f"Invalid ticker symbol: '{ticker}'")

    logger.info(f"Initialising financial research for {ticker}")
    await _emit_progress(state.get("report_id"), "init", 10, f"Fetching company info for {ticker}…")

    # Fetch company name and sector via YFinanceTool
    try:
        from app.tools.yfinance_tool import YFinanceTool
        yf = YFinanceTool()
        info = yf.get_company_info(ticker)
        company_name = info.get("name", ticker)
        sector = info.get("sector", "Unknown")
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Company info fetch failed: {exc}")
        company_name = ticker
        sector = "Unknown"

    return {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "errors": [],
        "completed_agents": [],
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def fundamentals_node(state: FinancialResearchState) -> dict:
    """Execute the FundamentalsAgent."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "fundamentals", 20, "Running fundamentals analysis…")
    from app.agents.fundamentals import FundamentalsAgent
    result = await FundamentalsAgent().run(state)
    await _emit_progress(report_id, "fundamentals", 35, "Fundamentals analysis complete.")
    return result


async def sentiment_node(state: FinancialResearchState) -> dict:
    """Execute the SentimentAgent."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "sentiment", 20, "Running sentiment analysis…")
    from app.agents.sentiment import SentimentAgent
    result = await SentimentAgent().run(state)
    await _emit_progress(report_id, "sentiment", 35, "Sentiment analysis complete.")
    return result


async def technical_node(state: FinancialResearchState) -> dict:
    """Execute the TechnicalAgent."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "technical", 20, "Running technical analysis…")
    from app.agents.technical import TechnicalAgent
    result = await TechnicalAgent().run(state)
    await _emit_progress(report_id, "technical", 35, "Technical analysis complete.")
    return result


async def competitor_node(state: FinancialResearchState) -> dict:
    """Execute the CompetitorAgent."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "competitor", 20, "Running competitor analysis…")
    from app.agents.competitor import CompetitorAgent
    result = await CompetitorAgent().run(state)
    await _emit_progress(report_id, "competitor", 35, "Competitor analysis complete.")
    return result


async def risk_node(state: FinancialResearchState) -> dict:
    """Execute the RiskAgent."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "risk", 20, "Running risk analysis…")
    from app.agents.risk import RiskAgent
    result = await RiskAgent().run(state)
    await _emit_progress(report_id, "risk", 35, "Risk analysis complete.")
    return result


async def aggregator_node(state: FinancialResearchState) -> dict:
    """Aggregate results from all parallel agents."""
    completed = state.get("completed_agents", [])
    logger.info(f"Aggregating results. Completed agents: {completed}")
    await _emit_progress(state.get("report_id"), "aggregator", 60, "Aggregating agent results…")
    return {"status": "aggregating"}


async def report_node(state: FinancialResearchState) -> dict:
    """Execute the ReportAgent to produce the final output."""
    report_id = state.get("report_id")
    await _emit_progress(report_id, "report", 75, "Generating final report…")
    from app.agents.report import ReportAgent
    result = await ReportAgent().run(state)
    await _emit_progress(report_id, "report", 90, "Report generation complete.")
    return result


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    """Build and compile the LangGraph StateGraph.

    Returns the compiled graph or a simple async callable fallback when
    LangGraph is not installed.
    """
    if not _LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available – using sequential fallback executor.")
        return _sequential_fallback

    graph = StateGraph(FinancialResearchState)

    # Add nodes
    graph.add_node("init", init_node)
    graph.add_node("fundamentals", fundamentals_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("technical", technical_node)
    graph.add_node("competitor", competitor_node)
    graph.add_node("risk", risk_node)
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("report", report_node)

    # Set entry point
    graph.set_entry_point("init")

    # Fan-out from init to 5 parallel agents
    for agent_node in ["fundamentals", "sentiment", "technical", "competitor", "risk"]:
        graph.add_edge("init", agent_node)
        graph.add_edge(agent_node, "aggregator")

    # Sequential tail
    graph.add_edge("aggregator", "report")
    graph.add_edge("report", END)

    return graph.compile()


async def _sequential_fallback(state: FinancialResearchState) -> FinancialResearchState:
    """Run all agents sequentially when LangGraph is unavailable."""
    state = dict(state)  # type: ignore[assignment]
    for fn in [
        init_node,
        fundamentals_node,
        sentiment_node,
        technical_node,
        competitor_node,
        risk_node,
        aggregator_node,
        report_node,
    ]:
        try:
            update = await fn(state)  # type: ignore[arg-type]
            state.update(update)
        except Exception as exc:
            logger.error(f"Node {fn.__name__} failed: {exc}")
            state.setdefault("errors", []).append(str(exc))
    return state  # type: ignore[return-value]


# Module-level compiled graph instance
financial_graph = build_graph()
