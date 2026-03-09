"""CompetitorAgent – peer comparison and moat analysis."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState
from app.tools.competitor_tool import CompetitorTool


class CompetitorAgent(BaseAgent):
    """Agent that compares a company against its peers."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._competitor = CompetitorTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run competitor analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"CompetitorAgent starting for {ticker}")

        try:
            peers = self._competitor.get_peers(ticker)
            comparison_table = self._competitor.compare_metrics(ticker, peers)

            subject = comparison_table.get(ticker, {})
            peer_rows = "\n".join(
                f"  {sym}: P/E={v.get('pe_ratio')}, Margin={v.get('net_margin')}, ROE={v.get('roe')}"
                for sym, v in comparison_table.items()
                if sym != ticker
            )

            prompt = (
                f"You are a competitive analyst. Compare {ticker} against its peers:\n"
                f"{ticker}: P/E={subject.get('pe_ratio')}, Net Margin={subject.get('net_margin')}, "
                f"ROE={subject.get('roe')}, Revenue Growth={subject.get('revenue_growth')}\n"
                f"Peers:\n{peer_rows}\n\n"
                f"Evaluate competitive position and economic moat. "
                f"Determine if the company is a leader, parity, or laggard relative to peers."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, peers),
            )
            competitive_position = self._assess_position(ticker, comparison_table)

            return {
                "competitor_data": {
                    "competitors": peers,
                    "comparison_table": comparison_table,
                    "competitive_position": competitive_position,
                    "moat_analysis": f"Based on metrics, {ticker} shows a {competitive_position} competitive position.",
                    "analysis_text": analysis_text,
                },
                "completed_agents": state.get("completed_agents", []) + ["competitor"],
            }
        except Exception as exc:
            self.logger.error(f"CompetitorAgent failed for {ticker}: {exc}")
            return {
                "competitor_data": self._mock_competitor(ticker),
                "errors": state.get("errors", []) + [f"CompetitorAgent: {exc}"],
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
            "comparison_table": {ticker: {"name": f"{ticker} (Mock)", "pe_ratio": 25.5}},
            "competitive_position": "leader",
            "moat_analysis": f"Mock moat analysis for {ticker}.",
            "analysis_text": f"Mock competitor analysis for {ticker}.",
        }
