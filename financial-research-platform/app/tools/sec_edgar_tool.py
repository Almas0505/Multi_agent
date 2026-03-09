"""SEC EDGAR data fetching tool using the free public API."""

from __future__ import annotations

import httpx
from loguru import logger


class SECEdgarTool:
    """Fetch SEC filings data from the public EDGAR API."""

    _EDGAR_BASE = "https://data.sec.gov"
    _HEADERS = {"User-Agent": "FinancialResearchPlatform research@example.com"}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_company_facts(self, ticker: str) -> dict:
        """Return company concept facts from SEC EDGAR."""
        try:
            # Resolve ticker → CIK
            cik = self._get_cik(ticker)
            if not cik:
                return self._mock_company_facts(ticker)

            url = f"{self._EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
            with httpx.Client(timeout=15, headers=self._HEADERS) as client:
                response = client.get(url)
                response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_company_facts failed for {ticker}: {exc}")
            return self._mock_company_facts(ticker)

    def get_annual_report_summary(self, ticker: str) -> str:
        """Return a brief textual summary derived from SEC annual filing data."""
        try:
            facts = self.get_company_facts(ticker)
            if not facts or "facts" not in facts:
                return self._mock_annual_summary(ticker)

            gaap = facts.get("facts", {}).get("us-gaap", {})
            revenues = gaap.get("Revenues", {}).get("units", {}).get("USD", [])
            net_income = gaap.get("NetIncomeLoss", {}).get("units", {}).get("USD", [])

            # Pick most recent annual entries (form == "10-K")
            annual_revenue = [
                e for e in revenues if e.get("form") == "10-K"
            ]
            annual_net_income = [
                e for e in net_income if e.get("form") == "10-K"
            ]

            last_rev = annual_revenue[-1]["val"] if annual_revenue else "N/A"
            last_ni = annual_net_income[-1]["val"] if annual_net_income else "N/A"

            return (
                f"SEC EDGAR Summary for {ticker}: "
                f"Most recent annual revenue: ${last_rev:,}" if isinstance(last_rev, int) else
                f"Most recent annual revenue: {last_rev}"
            ) + (
                f", Net income: ${last_ni:,}" if isinstance(last_ni, int) else
                f", Net income: {last_ni}"
            ) + "."
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_annual_report_summary failed for {ticker}: {exc}")
            return self._mock_annual_summary(ticker)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_cik(self, ticker: str) -> str | None:
        """Resolve a ticker symbol to a zero-padded CIK string."""
        try:
            url = f"{self._EDGAR_BASE}/submissions/CIK.json"
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            with httpx.Client(timeout=10, headers=self._HEADERS) as client:
                response = client.get(tickers_url)
                response.raise_for_status()
            data = response.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
            return None
        except Exception as exc:
            logger.warning(f"CIK lookup failed for {ticker}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Mock fallbacks
    # ------------------------------------------------------------------

    def _mock_company_facts(self, ticker: str) -> dict:
        return {
            "entityName": f"{ticker} Corporation (Mock)",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"end": "2023-09-30", "val": 383_285_000_000, "form": "10-K"},
                                {"end": "2022-09-30", "val": 394_328_000_000, "form": "10-K"},
                            ]
                        }
                    },
                    "NetIncomeLoss": {
                        "units": {
                            "USD": [
                                {"end": "2023-09-30", "val": 96_995_000_000, "form": "10-K"},
                                {"end": "2022-09-30", "val": 99_803_000_000, "form": "10-K"},
                            ]
                        }
                    },
                }
            },
        }

    def _mock_annual_summary(self, ticker: str) -> str:
        return (
            f"SEC EDGAR Summary for {ticker} (Mock): "
            "Most recent annual revenue: $383,285,000,000, "
            "Net income: $96,995,000,000. "
            "Company maintains strong cash flows and solid balance sheet."
        )
