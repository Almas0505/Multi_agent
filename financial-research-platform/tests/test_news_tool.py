"""Tests for NewsTool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.tools.news_tool import NewsTool


# ---------------------------------------------------------------------------
# get_news
# ---------------------------------------------------------------------------


def test_get_news_returns_list_of_dicts_with_title_key() -> None:
    """get_news should return a non-empty list of dicts each with a 'title' key."""
    tool = NewsTool()
    articles = tool.get_news("AAPL", "Apple Inc.")

    assert isinstance(articles, list)
    assert len(articles) > 0
    for article in articles:
        assert isinstance(article, dict)
        assert "title" in article, "Each article dict must have a 'title' key"


def test_get_news_returns_mock_when_no_api_key(monkeypatch) -> None:
    """When NEWS_API_KEY is not set, get_news returns mock data."""
    monkeypatch.setattr("app.tools.news_tool.settings", MagicMock(NEWS_API_KEY=None))
    tool = NewsTool()
    articles = tool.get_news("TSLA", "Tesla")
    assert len(articles) > 0
    assert all("title" in a for a in articles)


# ---------------------------------------------------------------------------
# compute_aggregate_sentiment
# ---------------------------------------------------------------------------


def test_compute_aggregate_sentiment_with_mixed_scores() -> None:
    """compute_aggregate_sentiment with mixed scores should aggregate correctly."""
    articles = [
        {"title": "Great earnings", "sentiment_score": 0.8},
        {"title": "Poor outlook", "sentiment_score": -0.5},
        {"title": "Neutral news", "sentiment_score": 0.0},
        {"title": "Strong growth", "sentiment_score": 0.9},
    ]
    result = NewsTool.compute_aggregate_sentiment(articles)

    assert "overall_score" in result
    assert "positive_count" in result
    assert "negative_count" in result
    assert "neutral_count" in result
    assert "sentiment_label" in result
    assert "top_positive" in result
    assert "top_negative" in result

    assert result["positive_count"] == 2
    assert result["negative_count"] == 1
    assert result["neutral_count"] == 1


def test_compute_aggregate_sentiment_label_is_valid() -> None:
    """sentiment_label must be one of BULLISH, BEARISH, NEUTRAL."""
    articles = [
        {"title": "Good news", "sentiment_score": 0.5},
        {"title": "Bad news", "sentiment_score": -0.1},
    ]
    result = NewsTool.compute_aggregate_sentiment(articles)
    assert result["sentiment_label"] in ("BULLISH", "BEARISH", "NEUTRAL")


def test_compute_aggregate_sentiment_bullish_label() -> None:
    """Overall score > 0.2 should yield BULLISH label."""
    articles = [
        {"title": "Excellent results", "sentiment_score": 0.8},
        {"title": "Strong performance", "sentiment_score": 0.7},
        {"title": "Positive guidance", "sentiment_score": 0.9},
    ]
    result = NewsTool.compute_aggregate_sentiment(articles)
    assert result["sentiment_label"] == "BULLISH"


def test_compute_aggregate_sentiment_bearish_label() -> None:
    """Overall score < -0.2 should yield BEARISH label."""
    articles = [
        {"title": "Missed earnings", "sentiment_score": -0.8},
        {"title": "CEO fired", "sentiment_score": -0.9},
        {"title": "Regulatory probe", "sentiment_score": -0.6},
    ]
    result = NewsTool.compute_aggregate_sentiment(articles)
    assert result["sentiment_label"] == "BEARISH"


def test_compute_aggregate_sentiment_empty_articles() -> None:
    """Empty articles list should return defaults with NEUTRAL label."""
    result = NewsTool.compute_aggregate_sentiment([])
    assert result["sentiment_label"] == "NEUTRAL"
    assert result["overall_score"] == 0.0
    assert result["positive_count"] == 0


# ---------------------------------------------------------------------------
# get_news_with_sentiment (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_news_with_sentiment_no_llm_returns_zero_scores() -> None:
    """Without an LLM, get_news_with_sentiment should return score=0.0 for all articles."""
    tool = NewsTool()
    articles = await tool.get_news_with_sentiment("AAPL", llm=None)

    assert isinstance(articles, list)
    for article in articles:
        assert "title" in article
        assert "sentiment_score" in article
        assert article["sentiment_score"] == 0.0


@pytest.mark.asyncio
async def test_get_news_with_sentiment_with_llm_calls_llm() -> None:
    """With an LLM provided, get_news_with_sentiment should use the LLM to score."""
    mock_response = MagicMock()
    mock_response.content = "0.7"
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    tool = NewsTool()
    articles = await tool.get_news_with_sentiment("AAPL", llm=mock_llm)

    assert isinstance(articles, list)
    assert len(articles) > 0
    # At least one article should have a non-zero score
    scores = [a["sentiment_score"] for a in articles]
    assert any(s != 0.0 for s in scores)
