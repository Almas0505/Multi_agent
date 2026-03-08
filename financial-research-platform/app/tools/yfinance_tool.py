"""YFinance data-fetching tool with tenacity retry and mock fallbacks."""

from __future__ import annotations

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YFINANCE_AVAILABLE = False


class YFinanceTool:
    """Wrapper around yfinance with retry logic and mock data fallbacks."""

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_company_info(self, ticker: str) -> dict:
        """Return basic company information for *ticker*."""
        if not _YFINANCE_AVAILABLE:
            return self._mock_company_info(ticker)
        try:
            info = yf.Ticker(ticker).info
            return {
                "name": info.get("longName", ticker),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "country": info.get("country", "Unknown"),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", "USD"),
            }
        except Exception as exc:
            logger.warning(f"YFinance get_company_info failed for {ticker}: {exc}")
            return self._mock_company_info(ticker)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_financial_metrics(self, ticker: str) -> dict:
        """Return key financial ratios for *ticker*."""
        if not _YFINANCE_AVAILABLE:
            return self._mock_financial_metrics(ticker)
        try:
            info = yf.Ticker(ticker).info
            return {
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "gross_margin": info.get("grossMargins"),
                "operating_margin": info.get("operatingMargins"),
                "net_margin": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "debt_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "free_cash_flow": info.get("freeCashflow"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            }
        except Exception as exc:
            logger.warning(f"YFinance get_financial_metrics failed for {ticker}: {exc}")
            return self._mock_financial_metrics(ticker)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_historical_prices(self, ticker: str, period: str = "1y") -> dict:
        """Return OHLCV price data as a serialisable dict."""
        if not _YFINANCE_AVAILABLE:
            return self._mock_historical_prices(ticker)
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty:
                return self._mock_historical_prices(ticker)
            return {
                "dates": [str(d.date()) for d in hist.index],
                "open": hist["Open"].tolist(),
                "high": hist["High"].tolist(),
                "low": hist["Low"].tolist(),
                "close": hist["Close"].tolist(),
                "volume": hist["Volume"].tolist(),
            }
        except Exception as exc:
            logger.warning(f"YFinance get_historical_prices failed for {ticker}: {exc}")
            return self._mock_historical_prices(ticker)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_financial_statements(self, ticker: str) -> dict:
        """Return income statement, balance sheet, and cash flow data."""
        if not _YFINANCE_AVAILABLE:
            return self._mock_financial_statements(ticker)
        try:
            t = yf.Ticker(ticker)
            income = t.financials
            balance = t.balance_sheet
            cashflow = t.cashflow
            return {
                "income_statement": income.to_dict() if not income.empty else {},
                "balance_sheet": balance.to_dict() if not balance.empty else {},
                "cash_flow": cashflow.to_dict() if not cashflow.empty else {},
            }
        except Exception as exc:
            logger.warning(f"YFinance get_financial_statements failed for {ticker}: {exc}")
            return self._mock_financial_statements(ticker)

    def get_peer_companies(self, ticker: str) -> list[str]:
        """Return a list of peer/competitor ticker symbols."""
        # yfinance does not expose peers directly; return a static mock map
        peers_map: dict[str, list[str]] = {
            "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
            "MSFT": ["AAPL", "GOOGL", "AMZN", "META"],
            "GOOGL": ["META", "MSFT", "AMZN", "AAPL"],
            "AMZN": ["MSFT", "GOOGL", "AAPL", "WMT"],
            "TSLA": ["F", "GM", "RIVN", "NIO"],
            "META": ["SNAP", "GOOGL", "TWTR", "PINS"],
        }
        return peers_map.get(ticker.upper(), ["SPY", "QQQ", "DIA"])

    # ------------------------------------------------------------------
    # Mock fallbacks
    # ------------------------------------------------------------------

    def _mock_company_info(self, ticker: str) -> dict:
        return {
            "name": f"{ticker} Corporation (Mock)",
            "sector": "Technology",
            "industry": "Software",
            "country": "United States",
            "website": f"https://www.{ticker.lower()}.com",
            "description": f"Mock description for {ticker}.",
            "employees": 50000,
            "market_cap": 1_000_000_000,
            "currency": "USD",
        }

    def _mock_financial_metrics(self, ticker: str) -> dict:
        return {
            "pe_ratio": 25.5,
            "pb_ratio": 6.2,
            "ps_ratio": 7.1,
            "ev_ebitda": 18.3,
            "gross_margin": 0.43,
            "operating_margin": 0.28,
            "net_margin": 0.25,
            "roe": 0.35,
            "roa": 0.18,
            "debt_equity": 1.5,
            "current_ratio": 1.8,
            "quick_ratio": 1.4,
            "revenue_growth": 0.08,
            "earnings_growth": 0.12,
            "free_cash_flow": 90_000_000_000,
            "dividend_yield": 0.005,
            "beta": 1.2,
            "52w_high": 200.0,
            "52w_low": 130.0,
            "current_price": 175.0,
        }

    def _mock_historical_prices(self, ticker: str) -> dict:
        import random
        from datetime import date, timedelta

        today = date.today()
        dates = [(today - timedelta(days=i)).isoformat() for i in range(252, 0, -1)]
        close = [150.0]
        for _ in range(251):
            close.append(round(close[-1] * (1 + random.uniform(-0.02, 0.02)), 2))
        return {
            "dates": dates,
            "open": [round(c * 0.99, 2) for c in close],
            "high": [round(c * 1.01, 2) for c in close],
            "low": [round(c * 0.98, 2) for c in close],
            "close": close,
            "volume": [random.randint(10_000_000, 100_000_000) for _ in close],
        }

    def _mock_financial_statements(self, ticker: str) -> dict:
        return {
            "income_statement": {
                "Total Revenue": {"2023": 383_285_000_000, "2022": 394_328_000_000},
                "Net Income": {"2023": 96_995_000_000, "2022": 99_803_000_000},
                "Gross Profit": {"2023": 169_148_000_000, "2022": 170_782_000_000},
            },
            "balance_sheet": {
                "Total Assets": {"2023": 352_583_000_000, "2022": 352_755_000_000},
                "Total Debt": {"2023": 109_280_000_000, "2022": 120_069_000_000},
                "Stockholders Equity": {"2023": 62_146_000_000, "2022": 50_672_000_000},
            },
            "cash_flow": {
                "Operating Cash Flow": {"2023": 110_543_000_000, "2022": 122_151_000_000},
                "Free Cash Flow": {"2023": 99_584_000_000, "2022": 111_443_000_000},
                "Capital Expenditure": {"2023": -10_959_000_000, "2022": -10_708_000_000},
            },
        }
