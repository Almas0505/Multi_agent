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
# Node functions
# ---------------------------------------------------------------------------

async def init_node(state: FinancialResearchState) -> dict:
    """Validate ticker and initialise workflow state."""
    ticker = state.get("ticker", "").strip().upper()
    if not ticker or len(ticker) > 10:
        raise ValueError(f"Invalid ticker symbol: '{ticker}'")

    logger.info(f"Initialising financial research for {ticker}")

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
    from app.agents.fundamentals import FundamentalsAgent
    agent = FundamentalsAgent()
    return await agent.run(state)


async def sentiment_node(state: FinancialResearchState) -> dict:
    """Execute the SentimentAgent."""
    from app.agents.sentiment import SentimentAgent
    agent = SentimentAgent()
    return await agent.run(state)


async def technical_node(state: FinancialResearchState) -> dict:
    """Execute the TechnicalAgent."""
    from app.agents.technical import TechnicalAgent
    agent = TechnicalAgent()
    return await agent.run(state)


async def competitor_node(state: FinancialResearchState) -> dict:
    """Execute the CompetitorAgent."""
    from app.agents.competitor import CompetitorAgent
    agent = CompetitorAgent()
    return await agent.run(state)


async def risk_node(state: FinancialResearchState) -> dict:
    """Execute the RiskAgent."""
    from app.agents.risk import RiskAgent
    agent = RiskAgent()
    return await agent.run(state)


async def aggregator_node(state: FinancialResearchState) -> dict:
    """Aggregate results from all parallel agents."""
    completed = state.get("completed_agents", [])
    logger.info(f"Aggregating results. Completed agents: {completed}")
    return {"status": "aggregating"}


async def report_node(state: FinancialResearchState) -> dict:
    """Execute the ReportAgent to produce the final output."""
    from app.agents.report import ReportAgent
    agent = ReportAgent()
    return await agent.run(state)


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
