"""Competitor / peer comparison tool."""

from __future__ import annotations

from loguru import logger

from app.tools.yfinance_tool import YFinanceTool


class CompetitorTool:
    """Retrieve peer companies and compare key financial metrics."""

    def __init__(self) -> None:
        self._yf = YFinanceTool()

    def get_peers(self, ticker: str) -> list[str]:
        """Return a list of peer ticker symbols for *ticker*."""
        return self._yf.get_peer_companies(ticker)

    def compare_metrics(self, ticker: str, peers: list[str]) -> dict:
        """Build a comparison table for *ticker* and its *peers*."""
        tickers = [ticker] + peers
        comparison: dict[str, dict] = {}

        for sym in tickers:
            try:
                metrics = self._yf.get_financial_metrics(sym)
                info = self._yf.get_company_info(sym)
                comparison[sym] = {
                    "name": info.get("name", sym),
                    "pe_ratio": metrics.get("pe_ratio"),
                    "pb_ratio": metrics.get("pb_ratio"),
                    "net_margin": metrics.get("net_margin"),
                    "roe": metrics.get("roe"),
                    "revenue_growth": metrics.get("revenue_growth"),
                    "debt_equity": metrics.get("debt_equity"),
                    "market_cap": info.get("market_cap"),
                    "current_price": metrics.get("current_price"),
                }
            except Exception as exc:
                logger.warning(f"CompetitorTool failed to fetch metrics for {sym}: {exc}")
                comparison[sym] = {"name": sym, "error": str(exc)}

        return comparison
