"""TechnicalAgent – price indicators, chart generation, trend analysis."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState
from app.tools.technical_indicators import TechnicalIndicatorsTool, TechnicalIndicators
from app.tools.yfinance_tool import YFinanceTool


class TechnicalAgent(BaseAgent):
    """Agent that performs technical analysis on price data."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._yf = YFinanceTool()
        self._ta = TechnicalIndicators()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run technical analysis for the ticker in *state*."""
        ticker = state["ticker"]
        self.logger.info(f"TechnicalAgent starting for {ticker}")

        try:
            # Use compute_all for real indicators
            indicators_data = self._ta.compute_all(ticker)

            # Generate the 3-panel technical chart
            chart_path = self._ta.generate_chart_from_indicators(ticker, indicators_data)

            trend_signal = self._ta.get_trend_signal(indicators_data)
            rating = "BUY" if trend_signal == "BULLISH" else ("SELL" if trend_signal == "BEARISH" else "HOLD")

            prompt = (
                f"You are a technical analyst. Analyse {ticker} with these indicators:\n"
                f"RSI(14): {indicators_data.get('rsi')}, "
                f"MACD: {indicators_data.get('macd')}, Signal: {indicators_data.get('signal_line')}, "
                f"BB Upper: {indicators_data.get('bb_upper')}, BB Lower: {indicators_data.get('bb_lower')}, "
                f"SMA20: {indicators_data.get('sma20')}, SMA50: {indicators_data.get('sma50')}\n"
                f"Support: {indicators_data.get('support')}, Resistance: {indicators_data.get('resistance')}\n"
                f"Trend Signal: {trend_signal}\n"
                f"Provide a concise technical analysis with trend direction and key levels."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, indicators_data, trend_signal),
            )

            return {
                "technical_data": {
                    "trend": trend_signal,
                    "trend_signal": trend_signal,
                    "rsi": indicators_data.get("rsi"),
                    "macd": indicators_data.get("macd"),
                    "signal_line": indicators_data.get("signal_line"),
                    "macd_signal": indicators_data.get("signal_line"),
                    "bb_upper": indicators_data.get("bb_upper"),
                    "bb_lower": indicators_data.get("bb_lower"),
                    "bb_middle": indicators_data.get("bb_middle"),
                    "sma20": indicators_data.get("sma20"),
                    "sma50": indicators_data.get("sma50"),
                    "support": indicators_data.get("support"),
                    "resistance": indicators_data.get("resistance"),
                    "support_levels": [indicators_data.get("support")] if indicators_data.get("support") else [],
                    "resistance_levels": [indicators_data.get("resistance")] if indicators_data.get("resistance") else [],
                    "bollinger_position": self._bb_position(indicators_data),
                    "chart_path": chart_path,
                    "analysis_text": analysis_text,
                    "rating": rating,
                },
                "price_data": state.get("price_data"),
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
        sma50 = indicators.get("sma_50") or indicators.get("sma50") or 0
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
            f"MACD shows {'bullish' if (indicators.get('macd', 0) or 0) > 0 else 'bearish'} momentum. "
            f"Support: {indicators.get('support')}, Resistance: {indicators.get('resistance')}."
        )

    def _mock_technical(self, ticker: str) -> dict:
        return {
            "trend": "BULLISH",
            "trend_signal": "BULLISH",
            "rsi": 55.3,
            "macd": 1.25,
            "signal_line": 0.98,
            "macd_signal": 0.98,
            "bb_upper": 185.0,
            "bb_lower": 165.0,
            "bb_middle": 175.0,
            "sma20": 174.0,
            "sma50": 172.5,
            "support": 165.0,
            "resistance": 185.0,
            "support_levels": [165.0, 160.0],
            "resistance_levels": [185.0, 190.0],
            "bollinger_position": "middle",
            "chart_path": "./charts/mock_chart.png",
            "analysis_text": f"Mock technical analysis for {ticker}.",
            "rating": "BUY",
        }
