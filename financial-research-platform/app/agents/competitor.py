
"""CompetitorAgent – peer comparison and moat analysis."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.errors import make_agent_error
from app.models.state import FinancialResearchState
from app.tools.competitor_tool import CompetitorTool
from app.tools.yfinance_tool import YFinanceTool


class CompetitorAgent(BaseAgent):
    """Agent that compares a company against its peers."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._competitor = CompetitorTool()
        self._yf = YFinanceTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run competitor analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"CompetitorAgent starting for {ticker}")

        try:
            peer_comparison = self._competitor.get_peer_comparison(ticker)
            peers = peer_comparison.get("peers", [])
            vs_peers = peer_comparison.get("vs_peers", {})

            # Get subject metrics for moat analysis
            subject_metrics = self._yf.get_financial_metrics(ticker)
            moat_analysis = self._competitor.get_moat_analysis(ticker, subject_metrics)

            # Build prompt table
            peer_rows = "\n".join(
                f"  {p['ticker']}: P/E={p.get('pe_ratio')}, "
                f"Margin={p.get('net_margin')}, ROE={p.get('roe')}, "
                f"Growth={p.get('revenue_growth')}"
                for p in peers
            )

            prompt = (
                f"You are a competitive analyst. Compare {ticker} against its peers:\n"
                f"{ticker}: P/E={subject_metrics.get('pe_ratio')}, "
                f"Net Margin={subject_metrics.get('net_margin')}, "
                f"ROE={subject_metrics.get('roe')}, "
                f"Revenue Growth={subject_metrics.get('revenue_growth')}\n"
                f"Peers:\n{peer_rows}\n\n"
                f"PE Percentile Rank: {vs_peers.get('pe_percentile')}, "
                f"Margin Rank: {vs_peers.get('margin_rank')}, "
                f"Growth Rank: {vs_peers.get('growth_rank')}\n\n"
                f"Moat: {moat_analysis}\n\n"
                f"Evaluate competitive position and provide a BUY/HOLD/SELL rating."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, [p["ticker"] for p in peers]),
            )

            # Rating based on vs_peers rankings (1-best to N-worst among subject+peers)
            # avg_rank <= 2: top-2 in most categories → BUY; >= 4: bottom → SELL; else HOLD
            avg_rank = (
                (vs_peers.get("pe_percentile", 3) +
                 vs_peers.get("margin_rank", 3) +
                 vs_peers.get("growth_rank", 3)) / 3
            )
            rating = "BUY" if avg_rank <= 2 else ("SELL" if avg_rank >= 4 else "HOLD")

            return {
                "competitor_data": {
                    "competitors": [p["ticker"] for p in peers],
                    "peers": peers,
                    "vs_peers": vs_peers,
                    "comparison_table": {ticker: subject_metrics, **{p["ticker"]: p for p in peers}},
                    "competitive_position": self._assess_position(ticker, {ticker: subject_metrics, **{p["ticker"]: p for p in peers}}),
                    "moat_analysis": moat_analysis,
                    "analysis_text": analysis_text,
                    "rating": rating,
                },
                "completed_agents": state.get("completed_agents", []) + ["competitor"],
            }
        except Exception as exc:
            self.logger.error(f"CompetitorAgent failed for {ticker}: {exc}")
            return {
                "competitor_data": self._mock_competitor(ticker),
                "errors": state.get("errors", []) + [make_agent_error("competitor", exc)],
                "completed_agents": state.get("completed_agents", []) + ["competitor"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assess_position(self, ticker: str, comparison: dict) -> str:
        subject = comparison.get(ticker, {})
        peers = [v for k, v in comparison.items() if k != ticker and "error" not in v]
        if not peers:
            return "leader"
        avg_margin = sum(p.get("net_margin") or 0 for p in peers) / len(peers)
        own_margin = subject.get("net_margin") or 0
        if own_margin > avg_margin * 1.1:
            return "leader"
        if own_margin < avg_margin * 0.9:
            return "laggard"
        return "parity"

    def _mock_analysis_text(self, ticker: str, peers: list[str]) -> str:
        return (
            f"{ticker} maintains a strong competitive position relative to peers "
            f"({', '.join(peers[:3])}). The company benefits from economies of scale, "
            f"brand strength, and a robust ecosystem that creates switching costs."
        )

    def _mock_competitor(self, ticker: str) -> dict:
        return {
            "competitors": ["MSFT", "GOOGL", "META"],
            "peers": [],
            "vs_peers": {"pe_percentile": 2, "margin_rank": 1, "growth_rank": 2},
            "comparison_table": {ticker: {"name": f"{ticker} (Mock)", "pe_ratio": 25.5}},
            "competitive_position": "leader",
            "moat_analysis": f"Mock moat analysis for {ticker}.",
            "analysis_text": f"Mock competitor analysis for {ticker}.",
            "rating": "HOLD",
        }
