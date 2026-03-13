"""RiskAgent – beta, VaR, max drawdown, regulatory risk analysis."""

from __future__ import annotations

import math

from app.agents.base import BaseAgent
from app.models.errors import make_agent_error
from app.models.state import FinancialResearchState
from app.tools.news_tool import NewsTool
from app.tools.yfinance_tool import YFinanceTool

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NUMPY_AVAILABLE = False


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
            # Fetch 2-year price data for real risk calculations
            price_data = self._yf.get_historical_prices(ticker, period="2y")
            spy_data = self._yf.get_historical_prices("SPY", period="2y")
            metrics = self._yf.get_financial_metrics(ticker)

            # Compute real risk metrics using numpy when available
            beta = self._calculate_beta_vs_spy(price_data, spy_data)
            var_95 = self._calculate_var_numpy(price_data)
            max_dd = self._calculate_max_drawdown(price_data)
            volatility = self._calculate_volatility(price_data)
            sharpe = self._calculate_sharpe(price_data)

            debt_level = self._assess_debt(metrics)
            news = self._news.get_news(ticker, state.get("company_name", ticker))
            reg_risks = self._extract_regulatory_risks(news)

            # Determine risk level based on beta and VaR thresholds
            # LOW: stable stocks with beta < 0.8 (below-market vol) and VaR > -2% (small daily loss)
            # HIGH: volatile stocks with beta > 1.5 or VaR < -4% (large potential daily loss)
            # MEDIUM: all other stocks
            if beta < 0.8 and var_95 > -0.02:
                risk_level = "LOW"
            elif beta > 1.5 or var_95 < -0.04:
                risk_level = "HIGH"
            else:
                risk_level = "MEDIUM"

            # Legacy risk_score for backward compatibility
            risk_score = self._compute_risk_score(beta, abs(var_95), max_dd, debt_level)

            key_risks = [
                f"Beta of {beta:.2f} indicates {'above' if beta > 1 else 'below'}-market volatility.",
                f"95% VaR: {var_95:.2%} daily downside risk.",
                f"Maximum drawdown: {max_dd:.2%}.",
                f"Annualised volatility: {volatility:.2%}.",
                f"Sharpe ratio: {sharpe:.2f}.",
                f"Debt-to-equity: {metrics.get('debt_equity', 'N/A')} ({debt_level}).",
            ] + reg_risks

            prompt = (
                f"You are a risk analyst. Assess the risk profile of {ticker}:\n"
                f"Beta: {beta:.2f}, VaR(95%): {var_95:.2%}, Max Drawdown: {max_dd:.2%}\n"
                f"Annualised Volatility: {volatility:.2%}, Sharpe Ratio: {sharpe:.2f}\n"
                f"Debt/Equity: {metrics.get('debt_equity')}, Risk Level: {risk_level}\n"
                f"Key risks: {'; '.join(key_risks[:3])}\n"
                f"Provide a concise risk assessment with a BUY/HOLD/SELL risk-adjusted rating."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, risk_score, risk_level),
            )

            # Rating based on risk level
            rating = "HOLD" if risk_level == "MEDIUM" else ("BUY" if risk_level == "LOW" else "SELL")

            return {
                "risk_data": {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "beta": round(beta, 4),
                    "var_95": round(var_95, 6),
                    "max_drawdown": round(max_dd, 6),
                    "volatility": round(volatility, 6),
                    "sharpe_ratio": round(sharpe, 4),
                    "key_risks": key_risks,
                    "analysis_text": analysis_text,
                    "rating": rating,
                },
                "completed_agents": state.get("completed_agents", []) + ["risk"],
            }
        except Exception as exc:
            self.logger.error(f"RiskAgent failed for {ticker}: {exc}")
            return {
                "risk_data": self._mock_risk(ticker),
                "errors": state.get("errors", []) + [make_agent_error("risk", exc)],
                "completed_agents": state.get("completed_agents", []) + ["risk"],
            }

    # ------------------------------------------------------------------
    # Private helpers – real numpy-based calculations
    # ------------------------------------------------------------------

    def _calculate_beta_vs_spy(self, price_data: dict, spy_data: dict) -> float:
        """Compute real beta: cov(stock_returns, spy_returns) / var(spy_returns)."""
        if not _NUMPY_AVAILABLE:
            return self._calculate_beta(price_data)
        try:
            stock_closes = np.array(price_data.get("close", []), dtype=float)
            spy_closes = np.array(spy_data.get("close", []), dtype=float)

            if len(stock_closes) < 20 or len(spy_closes) < 20:
                return self._calculate_beta(price_data)

            # Align lengths
            min_len = min(len(stock_closes), len(spy_closes))
            stock_closes = stock_closes[-min_len:]
            spy_closes = spy_closes[-min_len:]

            stock_returns = np.diff(stock_closes) / stock_closes[:-1]
            spy_returns = np.diff(spy_closes) / spy_closes[:-1]

            spy_var = np.var(spy_returns, ddof=1)
            if spy_var == 0:
                return 1.0
            cov = np.cov(stock_returns, spy_returns)[0, 1]
            return round(float(cov / spy_var), 4)
        except Exception:
            return self._calculate_beta(price_data)

    def _calculate_var_numpy(self, price_data: dict) -> float:
        """Compute 95% VaR as np.percentile(daily_returns, 5)."""
        if not _NUMPY_AVAILABLE:
            return -self._calculate_var(price_data)
        try:
            closes = np.array(price_data.get("close", []), dtype=float)
            if len(closes) < 20:
                return -0.025
            returns = np.diff(closes) / closes[:-1]
            return round(float(np.percentile(returns, 5)), 6)
        except Exception:
            return -0.025

    def _calculate_volatility(self, price_data: dict) -> float:
        """Annualised standard deviation of daily returns (std * sqrt(252))."""
        if not _NUMPY_AVAILABLE:
            return 0.20
        try:
            closes = np.array(price_data.get("close", []), dtype=float)
            if len(closes) < 20:
                return 0.20
            returns = np.diff(closes) / closes[:-1]
            return round(float(np.std(returns, ddof=1) * math.sqrt(252)), 6)
        except Exception:
            return 0.20

    def _calculate_sharpe(self, price_data: dict, risk_free: float = 0.05) -> float:
        """Sharpe ratio: (mean_return * 252 - risk_free) / (std * sqrt(252))."""
        if not _NUMPY_AVAILABLE:
            return 1.0
        try:
            closes = np.array(price_data.get("close", []), dtype=float)
            if len(closes) < 20:
                return 1.0
            returns = np.diff(closes) / closes[:-1]
            mean_r = float(np.mean(returns))
            std_r = float(np.std(returns, ddof=1))
            if std_r == 0:
                return 0.0
            return round((mean_r * 252 - risk_free) / (std_r * math.sqrt(252)), 4)
        except Exception:
            return 1.0

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
        """Calculate parametric 95% VaR from daily returns (returns positive value)."""
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
            "var_95": -0.025,
            "max_drawdown": 0.28,
            "volatility": 0.20,
            "sharpe_ratio": 1.0,
            "key_risks": [
                "Market volatility above average (beta > 1).",
                "Moderate leverage levels.",
                "Regulatory scrutiny in core markets.",
            ],
            "analysis_text": f"Mock risk analysis for {ticker}.",
            "rating": "HOLD",
        }
