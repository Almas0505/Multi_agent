"""FundamentalsAgent – analyses financial ratios, DCF, and SEC filings."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.errors import make_agent_error
from app.models.state import FinancialResearchState
from app.tools.sec_edgar_tool import SECEdgarTool
from app.tools.yfinance_tool import YFinanceTool


class FundamentalsAgent(BaseAgent):
    """Agent that performs fundamental financial analysis."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._yf = YFinanceTool()
        self._sec = SECEdgarTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run fundamental analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"FundamentalsAgent starting for {ticker}")

        try:
            metrics = self._yf.get_financial_metrics(ticker)
            sec_result = self._sec.get_annual_report_summary(ticker)
            # Support both dict (new) and str (legacy) return types
            if isinstance(sec_result, dict):
                sec_summary = sec_result.get("summary_text", str(sec_result))
            else:
                sec_summary = str(sec_result)

            # New Phase 2: real shares outstanding and income statement
            shares_outstanding = self._yf.get_shares_outstanding(ticker)
            income_summary = self._yf.get_income_statement_summary(ticker)
            revenue_trend = income_summary.get("revenue", {})

            dcf_value = self._compute_dcf(metrics, shares_outstanding)

            prompt = (
                f"You are a Wall Street fundamental analyst. "
                f"Analyse {ticker} based on these metrics:\n"
                f"P/E: {metrics.get('pe_ratio')}, P/B: {metrics.get('pb_ratio')}, "
                f"EV/EBITDA: {metrics.get('ev_ebitda')}, Net Margin: {metrics.get('net_margin')}, "
                f"ROE: {metrics.get('roe')}, D/E: {metrics.get('debt_equity')}, "
                f"Revenue Growth: {metrics.get('revenue_growth')}, FCF: {metrics.get('free_cash_flow')}\n"
                f"Revenue Trend: {revenue_trend}\n"
                f"Shares Outstanding: {shares_outstanding:,}\n"
                f"DCF Fair Value estimate: ${dcf_value:.2f}\n"
                f"SEC Summary: {sec_summary}\n"
                f"Provide a concise fundamental analysis with a BUY/HOLD/SELL rating."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, metrics, dcf_value),
            )

            rating = self._determine_rating(metrics, dcf_value)

            return {
                "fundamentals_data": {
                    "pe_ratio": metrics.get("pe_ratio"),
                    "pb_ratio": metrics.get("pb_ratio"),
                    "ev_ebitda": metrics.get("ev_ebitda"),
                    "revenue_growth": metrics.get("revenue_growth"),
                    "net_margin": metrics.get("net_margin"),
                    "free_cash_flow": metrics.get("free_cash_flow"),
                    "debt_equity": metrics.get("debt_equity"),
                    "roe": metrics.get("roe"),
                    "dcf_fair_value": dcf_value,
                    "analysis_text": analysis_text,
                    "rating": rating,
                    "sec_summary": sec_summary,
                    "shares_outstanding": shares_outstanding,
                    "revenue_trend": revenue_trend,
                },
                "completed_agents": state.get("completed_agents", []) + ["fundamentals"],
            }
        except Exception as exc:
            self.logger.error(f"FundamentalsAgent failed for {ticker}: {exc}")
            return {
                "fundamentals_data": self._mock_fundamentals(ticker),
                "errors": state.get("errors", []) + [make_agent_error("fundamentals", exc)],
                "completed_agents": state.get("completed_agents", []) + ["fundamentals"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_dcf(self, metrics: dict, shares_outstanding: int | None = None) -> float:
        """Simplified DCF based on FCF and growth assumptions."""
        fcf = metrics.get("free_cash_flow") or 90_000_000_000
        growth_rate = metrics.get("revenue_growth") or 0.08
        discount_rate = 0.10
        terminal_growth = 0.03
        shares = shares_outstanding or 15_000_000_000

        projected_fcf = sum(
            fcf * (1 + growth_rate) ** year / (1 + discount_rate) ** year
            for year in range(1, 6)
        )
        terminal_value = (
            fcf * (1 + growth_rate) ** 5 * (1 + terminal_growth)
            / (discount_rate - terminal_growth)
            / (1 + discount_rate) ** 5
        )
        enterprise_value = projected_fcf + terminal_value
        return round(enterprise_value / shares, 2)

    def _determine_rating(self, metrics: dict, dcf_value: float) -> str:
        current_price = metrics.get("current_price") or 175.0
        if dcf_value > current_price * 1.15:
            return "BUY"
        if dcf_value < current_price * 0.85:
            return "SELL"
        return "HOLD"

    def _mock_analysis_text(self, ticker: str, metrics: dict, dcf_value: float) -> str:
        return (
            f"{ticker} demonstrates solid fundamentals with a P/E of "
            f"{metrics.get('pe_ratio', 'N/A')} and net margin of "
            f"{metrics.get('net_margin', 'N/A'):.1%}. "
            f"DCF analysis suggests a fair value of ${dcf_value:.2f}. "
            f"The company shows strong free cash flow generation and a healthy balance sheet. "
            f"Rating: {self._determine_rating(metrics, dcf_value)}."
        )

    def _mock_fundamentals(self, ticker: str) -> dict:
        return {
            "pe_ratio": 25.5,
            "pb_ratio": 6.2,
            "ev_ebitda": 18.3,
            "revenue_growth": 0.08,
            "net_margin": 0.25,
            "free_cash_flow": 90_000_000_000,
            "debt_equity": 1.5,
            "roe": 0.35,
            "dcf_fair_value": 195.0,
            "analysis_text": f"Mock fundamental analysis for {ticker}.",
            "rating": "BUY",
            "sec_summary": f"Mock SEC summary for {ticker}.",
            "shares_outstanding": 15_000_000_000,
            "revenue_trend": {},
        }
