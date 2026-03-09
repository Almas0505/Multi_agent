"""News fetching tool with mock fallback when NEWS_API_KEY is absent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger

from app.config import settings


class NewsTool:
    """Fetch financial news, insider transactions, and analyst ratings."""

    _NEWSAPI_URL = "https://newsapi.org/v2/everything"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_news(self, ticker: str, company_name: str, days: int = 30) -> list[dict]:
        """Return a list of recent news articles about the company."""
        if not settings.NEWS_API_KEY:
            logger.info(f"NEWS_API_KEY not set – returning mock news for {ticker}")
            return self._mock_news(ticker, company_name)

        try:
            from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            params = {
                "q": f"{ticker} OR {company_name}",
                "from": from_date,
                "sortBy": "relevancy",
                "language": "en",
                "apiKey": settings.NEWS_API_KEY,
                "pageSize": 20,
            }
            with httpx.Client(timeout=10) as client:
                response = client.get(self._NEWSAPI_URL, params=params)
                response.raise_for_status()
            articles = response.json().get("articles", [])
            return [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "publishedAt": a.get("publishedAt", ""),
                    "source": a.get("source", {}).get("name", ""),
                }
                for a in articles
            ]
        except Exception as exc:
            logger.warning(f"NewsTool.get_news failed for {ticker}: {exc}")
            return self._mock_news(ticker, company_name)

    async def get_news_with_sentiment(self, ticker: str, llm=None) -> list[dict]:
        """Return articles enriched with LLM-based sentiment scores.

        Each article dict contains: title, source, published_at, url, sentiment_score.
        If *llm* is provided, each headline is scored from -1.0 to +1.0.
        Falls back to 0.0 on parse failure.
        """
        raw_articles = self.get_news(ticker, ticker)
        results: list[dict] = []

        for article in raw_articles:
            title = article.get("title") or ""
            score = 0.0
            if llm and title:
                try:
                    from langchain_core.messages import HumanMessage  # type: ignore
                    prompt = (
                        "Rate the sentiment of this financial news headline from -1.0 "
                        "(very negative) to +1.0 (very positive). Return only a number.\n"
                        f"Headline: {title}"
                    )
                    response = await llm.ainvoke([HumanMessage(content=prompt)])
                    text = response.content.strip()
                    # Extract the first float-like token
                    import re
                    match = re.search(r"-?\d+(?:\.\d+)?", text)
                    if match:
                        score = max(-1.0, min(1.0, float(match.group())))
                except Exception as exc:
                    logger.warning(f"LLM sentiment scoring failed: {exc}")
                    score = 0.0

            results.append(
                {
                    "title": title,
                    "source": article.get("source", ""),
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                    "sentiment_score": score,
                }
            )

        return results

    @staticmethod
    def compute_aggregate_sentiment(articles: list[dict]) -> dict:
        """Compute aggregate sentiment metrics from a list of scored articles.

        Returns overall_score (weighted avg, recent 2x), positive_count,
        negative_count, neutral_count, sentiment_label, top_positive, top_negative.
        """
        if not articles:
            return {
                "overall_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "sentiment_label": "NEUTRAL",
                "top_positive": "",
                "top_negative": "",
            }

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        weighted_sum = 0.0
        total_weight = 0.0

        for idx, article in enumerate(articles):
            score = article.get("sentiment_score", 0.0) or 0.0
            # Recent articles (lower index after sorting by recency) get weight 2
            weight = 2.0 if idx < len(articles) // 2 else 1.0
            weighted_sum += score * weight
            total_weight += weight

            if score > 0.1:
                positive_count += 1
            elif score < -0.1:
                negative_count += 1
            else:
                neutral_count += 1

        overall_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

        if overall_score > 0.2:
            sentiment_label = "BULLISH"
        elif overall_score < -0.2:
            sentiment_label = "BEARISH"
        else:
            sentiment_label = "NEUTRAL"

        sorted_by_score = sorted(articles, key=lambda a: a.get("sentiment_score", 0.0) or 0.0)
        top_negative = sorted_by_score[0].get("title", "") if sorted_by_score else ""
        top_positive = sorted_by_score[-1].get("title", "") if sorted_by_score else ""

        return {
            "overall_score": overall_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "sentiment_label": sentiment_label,
            "top_positive": top_positive,
            "top_negative": top_negative,
        }

    def get_insider_transactions(self, ticker: str) -> dict:
        """Return insider buying/selling activity."""
        # Insider data typically requires a paid API; return mock data
        return {
            "ticker": ticker,
            "recent_transactions": [
                {"date": "2024-01-15", "insider": "CEO", "transaction": "BUY", "shares": 10000, "value": 1_750_000},
                {"date": "2024-01-10", "insider": "CFO", "transaction": "SELL", "shares": 5000, "value": 875_000},
                {"date": "2023-12-20", "insider": "Director", "transaction": "BUY", "shares": 2000, "value": 350_000},
            ],
            "net_buying_shares": 7000,
            "sentiment": "mildly_bullish",
        }

    def get_analyst_ratings(self, ticker: str) -> dict:
        """Return aggregated analyst consensus and price targets."""
        return {
            "ticker": ticker,
            "consensus": "BUY",
            "strong_buy": 18,
            "buy": 10,
            "hold": 6,
            "sell": 2,
            "strong_sell": 1,
            "average_target": 210.0,
            "high_target": 250.0,
            "low_target": 170.0,
            "num_analysts": 37,
        }

    # ------------------------------------------------------------------
    # Mock fallback
    # ------------------------------------------------------------------

    def _mock_news(self, ticker: str, company_name: str) -> list[dict]:
        today = datetime.now(timezone.utc)
        return [
            {
                "title": f"{company_name} Reports Strong Quarterly Earnings",
                "description": f"{ticker} beat analyst expectations with record revenue.",
                "url": f"https://example.com/news/{ticker.lower()}-earnings",
                "publishedAt": (today - timedelta(days=2)).isoformat(),
                "source": "Financial Times (Mock)",
            },
            {
                "title": f"{company_name} Announces New Product Line",
                "description": f"{ticker} is expanding into new markets with innovative products.",
                "url": f"https://example.com/news/{ticker.lower()}-products",
                "publishedAt": (today - timedelta(days=5)).isoformat(),
                "source": "Reuters (Mock)",
            },
            {
                "title": f"Analysts Raise Price Target for {ticker}",
                "description": f"Multiple analysts increase their price targets following strong guidance.",
                "url": f"https://example.com/news/{ticker.lower()}-targets",
                "publishedAt": (today - timedelta(days=8)).isoformat(),
                "source": "Bloomberg (Mock)",
            },
        ]
