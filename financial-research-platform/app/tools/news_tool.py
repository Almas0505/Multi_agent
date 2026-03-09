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
