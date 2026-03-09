"""SentimentAgent – analyses news sentiment, insider activity, analyst consensus."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState
from app.tools.news_tool import NewsTool


class SentimentAgent(BaseAgent):
    """Agent that evaluates market sentiment from multiple sources."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)
        self._news = NewsTool()

    async def run(self, state: FinancialResearchState) -> dict:
        """Run sentiment analysis for the ticker in *state*."""
        ticker = state["ticker"]
        company_name = state.get("company_name", ticker)
        self.logger.info(f"SentimentAgent starting for {ticker}")

        try:
            articles = self._news.get_news(ticker, company_name)
            insider = self._news.get_insider_transactions(ticker)
            analyst = self._news.get_analyst_ratings(ticker)

            headlines = "\n".join(f"- {a['title']}" for a in articles[:10])
            prompt = (
                f"Analyse the market sentiment for {ticker} ({company_name}) based on the following "
                f"recent news headlines:\n{headlines}\n\n"
                f"Insider activity: {insider['sentiment']}\n"
                f"Analyst consensus: {analyst['consensus']} "
                f"(Buy: {analyst['strong_buy'] + analyst['buy']}, "
                f"Hold: {analyst['hold']}, Sell: {analyst['sell'] + analyst['strong_sell']})\n\n"
                f"Return a sentiment score from 0 (very bearish) to 10 (very bullish) "
                f"and a brief analysis."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, analyst),
            )

            sentiment_score = self._score_from_analyst(analyst)
            top_news = articles[:5]

            return {
                "sentiment_data": {
                    "sentiment_score": sentiment_score,
                    "news_sentiment": "positive" if sentiment_score >= 6 else ("negative" if sentiment_score <= 4 else "neutral"),
                    "insider_activity": insider,
                    "analyst_consensus": analyst,
                    "top_news": top_news,
                    "analysis_text": analysis_text,
                },
                "completed_agents": state.get("completed_agents", []) + ["sentiment"],
            }
        except Exception as exc:
            self.logger.error(f"SentimentAgent failed for {ticker}: {exc}")
            return {
                "sentiment_data": self._mock_sentiment(ticker),
                "errors": state.get("errors", []) + [f"SentimentAgent: {exc}"],
                "completed_agents": state.get("completed_agents", []) + ["sentiment"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _score_from_analyst(self, analyst: dict) -> float:
        """Derive a 0-10 score from analyst consensus data."""
        total = analyst.get("num_analysts", 1) or 1
        bullish = analyst.get("strong_buy", 0) + analyst.get("buy", 0)
        bearish = analyst.get("sell", 0) + analyst.get("strong_sell", 0)
        score = 5.0 + (bullish - bearish) / total * 5
        return round(min(10.0, max(0.0, score)), 1)

    def _mock_analysis_text(self, ticker: str, analyst: dict) -> str:
        return (
            f"Sentiment analysis for {ticker}: Overall sentiment is positive. "
            f"Analyst consensus is {analyst.get('consensus', 'BUY')} with an average "
            f"price target of ${analyst.get('average_target', 210)}. "
            f"Insider activity shows net buying, indicating management confidence."
        )

    def _mock_sentiment(self, ticker: str) -> dict:
        return {
            "sentiment_score": 7.2,
            "news_sentiment": "positive",
            "insider_activity": {"sentiment": "mildly_bullish"},
            "analyst_consensus": {"consensus": "BUY", "average_target": 210.0},
            "top_news": [],
            "analysis_text": f"Mock sentiment analysis for {ticker}.",
        }
