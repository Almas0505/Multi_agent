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

    def get_peer_comparison(self, ticker: str) -> dict:
        """Return a structured peer comparison dict with percentile rankings.

        Returns::
            {
                "subject": ticker,
                "peers": [{"ticker": ..., "pe_ratio": ..., ...}, ...],
                "vs_peers": {
                    "pe_percentile": ...,
                    "margin_rank": ...,
                    "growth_rank": ...,
                },
            }
        """
        try:
            peer_list = self._yf.get_peer_companies(ticker)[:5]
            peers_data: list[dict] = []

            for sym in peer_list:
                try:
                    metrics = self._yf.get_financial_metrics(sym)
                    peers_data.append(
                        {
                            "ticker": sym,
                            "pe_ratio": metrics.get("pe_ratio"),
                            "pb_ratio": metrics.get("pb_ratio"),
                            "net_margin": metrics.get("net_margin"),
                            "revenue_growth": metrics.get("revenue_growth"),
                            "market_cap": metrics.get("market_cap") or self._yf.get_company_info(sym).get("market_cap"),
                            "roe": metrics.get("roe"),
                        }
                    )
                except Exception as exc:
                    logger.warning(f"get_peer_comparison: failed for peer {sym}: {exc}")

            # Subject metrics
            subject_metrics = self._yf.get_financial_metrics(ticker)

            # Compute percentile rankings among subject + peers
            all_entries = [{"ticker": ticker, **subject_metrics}] + peers_data

            def _rank(key: str, ascending: bool = True) -> int:
                """Return 1-based rank of subject among all entries (lower is better if ascending)."""
                values = [(e.get(key) or 0) for e in all_entries]
                subject_val = values[0]
                rank = sum(1 for v in values if (v < subject_val if not ascending else v > subject_val)) + 1
                return rank

            vs_peers = {
                "pe_percentile": _rank("pe_ratio", ascending=True),   # lower PE is better
                "margin_rank": _rank("net_margin", ascending=False),    # higher margin is better
                "growth_rank": _rank("revenue_growth", ascending=False),
            }

            return {
                "subject": ticker,
                "peers": peers_data,
                "vs_peers": vs_peers,
            }
        except Exception as exc:
            logger.warning(f"get_peer_comparison failed for {ticker}: {exc}")
            return {
                "subject": ticker,
                "peers": [],
                "vs_peers": {"pe_percentile": 1, "margin_rank": 1, "growth_rank": 1},
            }

    def get_moat_analysis(self, ticker: str, metrics: dict) -> str:
        """Generate a text moat assessment based on key financial metrics."""
        net_margin = metrics.get("net_margin") or 0
        roe = metrics.get("roe") or 0
        revenue_growth = metrics.get("revenue_growth") or 0

        moat_signals: list[str] = []
        if net_margin > 0.20:
            moat_signals.append("strong pricing power (net margin > 20%)")
        if roe > 0.25:
            moat_signals.append("high return on equity (ROE > 25%)")
        if revenue_growth > 0.10:
            moat_signals.append("above-average revenue growth (> 10% YoY)")

        if len(moat_signals) >= 3:
            moat_strength = "Wide"
        elif len(moat_signals) >= 1:
            moat_strength = "Narrow"
        else:
            moat_strength = "No discernible"

        if moat_signals:
            signals_text = ", ".join(moat_signals)
            return (
                f"{ticker} demonstrates a {moat_strength} economic moat, supported by "
                f"{signals_text}. These characteristics suggest durable competitive advantages."
            )
        return (
            f"{ticker} shows {moat_strength} economic moat based on current metrics. "
            f"Net margin: {net_margin:.1%}, ROE: {roe:.1%}, Revenue Growth: {revenue_growth:.1%}."
        )
