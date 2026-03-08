"""TechnicalAgent – price indicators, chart generation, trend analysis."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState
from app.tools.technical_indicators import TechnicalIndicatorsTool
from app.tools.yfinance_tool import YFinanceTool


class TechnicalAgent(BaseAgent):
    """Agent that performs technical analysis on price data."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._yf = YFinanceTool()
        self._ta = TechnicalIndicatorsTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run technical analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"TechnicalAgent starting for {ticker}")

        try:
            price_data = state.get("price_data") or self._yf.get_historical_prices(ticker)
            indicators = self._ta.calculate_indicators(price_data)
            levels = self._ta.find_support_resistance(price_data)
            chart_path = self._ta.generate_chart(price_data, ticker)

            trend = self._determine_trend(indicators)

            prompt = (
                f"You are a technical analyst. Analyse {ticker} with these indicators:\n"
                f"RSI: {indicators.get('rsi')}, MACD: {indicators.get('macd')}, "
                f"MACD Signal: {indicators.get('macd_signal')}, "
                f"SMA50: {indicators.get('sma_50')}, SMA200: {indicators.get('sma_200')}, "
                f"BB Upper: {indicators.get('bb_upper')}, BB Lower: {indicators.get('bb_lower')}\n"
                f"Support: {levels.get('support_levels')}\n"
                f"Resistance: {levels.get('resistance_levels')}\n"
                f"Provide a concise technical analysis with trend direction."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, indicators, trend),
            )

            return {
                "technical_data": {
                    "trend": trend,
                    "rsi": indicators.get("rsi"),
                    "macd_signal": indicators.get("macd_signal"),
                    "support_levels": levels.get("support_levels"),
                    "resistance_levels": levels.get("resistance_levels"),
                    "bollinger_position": self._bb_position(indicators),
                    "sma_50": indicators.get("sma_50"),
                    "sma_200": indicators.get("sma_200"),
                    "chart_path": chart_path,
                    "analysis_text": analysis_text,
                },
                "price_data": price_data,
                "completed_agents": state.get("completed_agents", []) + ["technical"],
            }
        except Exception as exc:
            self.logger.error(f"TechnicalAgent failed for {ticker}: {exc}")
            return {
                "technical_data": self._mock_technical(ticker),
                "errors": state.get("errors", []) + [f"TechnicalAgent: {exc}"],
                "completed_agents": state.get("completed_agents", []) + ["technical"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _determine_trend(self, indicators: dict) -> str:
        sma50 = indicators.get("sma_50") or 0
        sma200 = indicators.get("sma_200") or 0
        current = indicators.get("current_price") or 0
        if current > sma50 > sma200:
            return "BULLISH"
        if current < sma50 < sma200:
            return "BEARISH"
        return "NEUTRAL"

    def _bb_position(self, indicators: dict) -> str:
        current = indicators.get("current_price") or 0
        bb_upper = indicators.get("bb_upper") or float("inf")
        bb_lower = indicators.get("bb_lower") or 0
        if current >= bb_upper:
            return "overbought"
        if current <= bb_lower:
            return "oversold"
        return "middle"

    def _mock_analysis_text(self, ticker: str, indicators: dict, trend: str) -> str:
        return (
            f"Technical analysis for {ticker}: The stock is in a {trend} trend. "
            f"RSI at {indicators.get('rsi', 55)} suggests "
            f"{'overbought conditions' if (indicators.get('rsi') or 0) > 70 else 'normal momentum'}. "
            f"MACD shows {'bullish' if (indicators.get('macd', 0) or 0) > 0 else 'bearish'} momentum."
        )

    def _mock_technical(self, ticker: str) -> dict:
        return {
            "trend": "BULLISH",
            "rsi": 55.3,
            "macd_signal": 0.98,
            "support_levels": [165.0, 160.0],
            "resistance_levels": [185.0, 190.0],
            "bollinger_position": "middle",
            "sma_50": 172.5,
            "sma_200": 160.0,
            "chart_path": "./charts/mock_chart.png",
            "analysis_text": f"Mock technical analysis for {ticker}.",
        }
