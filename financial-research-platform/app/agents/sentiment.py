"""SentimentAgent – analyses news sentiment, insider activity, analyst consensus."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.errors import make_agent_error
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
            # Use LLM-scored sentiment articles
            articles = await self._news.get_news_with_sentiment(ticker, llm=self.llm)
            agg = self._news.compute_aggregate_sentiment(articles)

            insider = self._news.get_insider_transactions(ticker)
            analyst = self._news.get_analyst_ratings(ticker)

            overall_score = agg.get("overall_score", 0.0)
            sentiment_label = agg.get("sentiment_label", "NEUTRAL")

            prompt = (
                f"Analyse the market sentiment for {ticker} ({company_name}):\n"
                f"Aggregate Sentiment Score: {overall_score:.2f} (range -1 to +1)\n"
                f"Sentiment Label: {sentiment_label}\n"
                f"Positive articles: {agg.get('positive_count')}, "
                f"Negative: {agg.get('negative_count')}, Neutral: {agg.get('neutral_count')}\n"
                f"Top positive headline: {agg.get('top_positive')}\n"
                f"Top negative headline: {agg.get('top_negative')}\n"
                f"Insider activity: {insider.get('sentiment')}\n"
                f"Analyst consensus: {analyst.get('consensus')} "
                f"(Buy: {analyst.get('strong_buy', 0) + analyst.get('buy', 0)}, "
                f"Hold: {analyst.get('hold', 0)}, Sell: {analyst.get('sell', 0) + analyst.get('strong_sell', 0)})\n\n"
                f"Provide a concise sentiment analysis."
            )
            analysis_text = await self._invoke_llm(
                prompt,
                fallback=self._mock_analysis_text(ticker, analyst),
            )

            # Convert -1..+1 score to 0..10 legacy scale for backward compatibility
            legacy_score = round((overall_score + 1) / 2 * 10, 1)

            # Determine rating from sentiment label
            rating_map = {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "HOLD"}
            rating = rating_map.get(sentiment_label, "HOLD")

            return {
                "sentiment_data": {
                    "sentiment_score": legacy_score,
                    "sentiment_label": sentiment_label,
                    "news_count": len(articles),
                    "top_positive_headline": agg.get("top_positive", ""),
                    "top_negative_headline": agg.get("top_negative", ""),
                    "news_sentiment": "positive" if legacy_score >= 6 else ("negative" if legacy_score <= 4 else "neutral"),
                    "insider_activity": insider,
                    "analyst_consensus": analyst,
                    "top_news": articles[:5],
                    "analysis_text": analysis_text,
                    "rating": rating,
                },
                "completed_agents": state.get("completed_agents", []) + ["sentiment"],
            }
        except Exception as exc:
            self.logger.error(f"SentimentAgent failed for {ticker}: {exc}")
            return {
                "sentiment_data": self._mock_sentiment(ticker),
                "errors": state.get("errors", []) + [make_agent_error("sentiment", exc)],
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
            "sentiment_label": "BULLISH",
            "news_count": 3,
            "top_positive_headline": "Strong earnings beat expectations.",
            "top_negative_headline": "Regulatory scrutiny concerns.",
            "news_sentiment": "positive",
            "insider_activity": {"sentiment": "mildly_bullish"},
            "analyst_consensus": {"consensus": "BUY", "average_target": 210.0},
            "top_news": [],
            "analysis_text": f"Mock sentiment analysis for {ticker}.",
            "rating": "BUY",
        }
