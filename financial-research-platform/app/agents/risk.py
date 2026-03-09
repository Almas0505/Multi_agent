"""RiskAgent – beta, VaR, max drawdown, regulatory risk analysis."""

from __future__ import annotations

import math

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState
from app.tools.news_tool import NewsTool
from app.tools.yfinance_tool import YFinanceTool


class RiskAgent(BaseAgent):
    """Agent that quantifies financial and operational risks."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._yf = YFinanceTool()
        self._news = NewsTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run risk analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"RiskAgent starting for {ticker}")

        try:
            price_data = state.get("price_data") or self._yf.get_historical_prices(ticker)
            metrics = self._yf.get_financial_metrics(ticker)

            beta = metrics.get("beta") or self._calculate_beta(price_data)
            var_95 = self._calculate_var(price_data)
            max_dd = self._calculate_max_drawdown(price_data)
            debt_level = self._assess_debt(metrics)
            news = self._news.get_news(ticker, state.get("company_name", ticker))
            reg_risks = self._extract_regulatory_risks(news)

            risk_score = self._compute_risk_score(beta, var_95, max_dd, debt_level)
            risk_level = "HIGH" if risk_score >= 7 else ("MEDIUM" if risk_score >= 4 else "LOW")

            key_risks = [
                f"Beta of {beta:.2f} indicates {'above' if beta > 1 else 'below'}-market volatility.",
                f"95% VaR: {var_95:.2%} daily downside risk.",
                f"Maximum drawdown: {max_dd:.2%}.",
                f"Debt-to-equity: {metrics.get('debt_equity', 'N/A')} ({debt_level}).",
            ] + reg_risks

            prompt = (
                f"You are a risk analyst. Assess the risk profile of {ticker}:\n"
                f"Beta: {beta:.2f}, VaR(95%): {var_95:.2%}, Max Drawdown: {max_dd:.2%}\n"
                f"Debt/Equity: {metrics.get('debt_equity')}\n"
                f"Key risks identified: {'; '.join(key_risks[:3])}\n"
                f"Provide a concise risk assessment with an overall risk score (0-10)."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, risk_score, risk_level),
            )

            return {
                "risk_data": {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "beta": round(beta, 4),
                    "var_95": round(var_95, 6),
                    "max_drawdown": round(max_dd, 6),
                    "key_risks": key_risks,
                    "analysis_text": analysis_text,
                },
                "completed_agents": state.get("completed_agents", []) + ["risk"],
            }
        except Exception as exc:
            self.logger.error(f"RiskAgent failed for {ticker}: {exc}")
            return {
                "risk_data": self._mock_risk(ticker),
                "errors": state.get("errors", []) + [f"RiskAgent: {exc}"],
                "completed_agents": state.get("completed_agents", []) + ["risk"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_beta(self, price_data: dict) -> float:
        """Estimate beta using price returns variance (simplified, no market data)."""
        closes = price_data.get("close", [])
        if len(closes) < 20:
            return 1.2
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
        ]
        variance = sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns)
        market_variance = 0.0002  # approximate S&P 500 daily variance
        return round(variance / market_variance, 4) if market_variance else 1.0

    def _calculate_var(self, price_data: dict, confidence: float = 0.95) -> float:
        """Calculate parametric 95% VaR from daily returns."""
        closes = price_data.get("close", [])
        if len(closes) < 20:
            return 0.025
        returns = sorted(
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
        )
        index = int((1 - confidence) * len(returns))
        return abs(returns[index])

    def _calculate_max_drawdown(self, price_data: dict) -> float:
        """Calculate the maximum peak-to-trough drawdown."""
        closes = price_data.get("close", [])
        if not closes:
            return 0.20
        peak = closes[0]
        max_dd = 0.0
        for price in closes:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        return max_dd

    def _assess_debt(self, metrics: dict) -> str:
        de = metrics.get("debt_equity") or 0
        if de > 3:
            return "HIGH"
        if de > 1.5:
            return "MODERATE"
        return "LOW"

    def _extract_regulatory_risks(self, news: list[dict]) -> list[str]:
        risk_keywords = ["lawsuit", "regulation", "fine", "investigation", "ban", "antitrust"]
        risks = []
        for article in news:
            title = (article.get("title") or "").lower()
            if any(kw in title for kw in risk_keywords):
                risks.append(f"Regulatory risk: {article['title'][:80]}")
        return risks[:3]

    def _compute_risk_score(self, beta: float, var_95: float, max_dd: float, debt_level: str) -> float:
        score = 0.0
        score += min(3.0, beta * 1.5)
        score += min(3.0, var_95 * 100)
        score += min(2.0, max_dd * 10)
        score += {"HIGH": 2.0, "MODERATE": 1.0, "LOW": 0.0}.get(debt_level, 0.0)
        return round(min(10.0, score), 1)

    def _mock_analysis_text(self, ticker: str, risk_score: float, risk_level: str) -> str:
        return (
            f"Risk assessment for {ticker}: Overall risk score is {risk_score}/10 ({risk_level}). "
            f"The company faces moderate market risk with manageable leverage. "
            f"Regulatory environment is stable with no near-term material risks identified."
        )

    def _mock_risk(self, ticker: str) -> dict:
        return {
            "risk_score": 4.5,
            "risk_level": "MEDIUM",
            "beta": 1.2,
            "var_95": 0.025,
            "max_drawdown": 0.28,
            "key_risks": [
                "Market volatility above average (beta > 1).",
                "Moderate leverage levels.",
                "Regulatory scrutiny in core markets.",
            ],
            "analysis_text": f"Mock risk analysis for {ticker}.",
        }
