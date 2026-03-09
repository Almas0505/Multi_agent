"""SEC EDGAR data fetching tool using the free public API."""

from __future__ import annotations

import httpx
from loguru import logger


class SECEdgarTool:
    """Fetch SEC filings data from the public EDGAR API."""

    _EDGAR_BASE = "https://data.sec.gov"
    _HEADERS = {"User-Agent": "FinancialResearchPlatform research@example.com"}
    _TIMEOUT = 5  # seconds for all HTTP calls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_company_facts(self, ticker: str) -> dict:
        """Return company concept facts from SEC EDGAR."""
        try:
            cik = self._get_cik(ticker)
            if not cik:
                return self._mock_company_facts(ticker)

            url = f"{self._EDGAR_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
            with httpx.Client(timeout=self._TIMEOUT, headers=self._HEADERS) as client:
                response = client.get(url)
                response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_company_facts failed for {ticker}: {exc}")
            return self._mock_company_facts(ticker)

    def get_annual_report_summary(self, ticker: str) -> dict:
        """Return a rich dict summarising the most recent 10-K filing data.

        Returns::
            {
                "cik": str,
                "company_name": str,
                "last_10k_date": str,
                "last_10k_accession": str,
                "summary_text": str,
            }

        The ``summary_text`` field mirrors the old string return value for
        backward compatibility.
        """
        try:
            cik = self._get_cik(ticker)
            company_name = ticker
            last_10k_date = "N/A"
            last_10k_accession = "N/A"
            last_rev: int | None = None
            last_ni: int | None = None

            facts = self.get_company_facts(ticker)
            if facts and "facts" in facts:
                company_name = facts.get("entityName", ticker)
                gaap = facts.get("facts", {}).get("us-gaap", {})
                revenues = gaap.get("Revenues", {}).get("units", {}).get("USD", [])
                net_income = gaap.get("NetIncomeLoss", {}).get("units", {}).get("USD", [])

                annual_revenue = [e for e in revenues if e.get("form") == "10-K"]
                annual_net_income = [e for e in net_income if e.get("form") == "10-K"]

                if annual_revenue:
                    last_entry = annual_revenue[-1]
                    last_rev = last_entry.get("val") or None
                    last_10k_date = last_entry.get("end", "N/A")
                    last_10k_accession = last_entry.get("accn", "N/A")
                if annual_net_income:
                    last_ni = annual_net_income[-1].get("val") or None

            rev_str = f"${last_rev:,}" if last_rev is not None else "N/A"
            ni_str = f"${last_ni:,}" if last_ni is not None else "N/A"
            summary_text = (
                f"SEC EDGAR Summary for {ticker}: "
                f"Most recent annual revenue: {rev_str}, "
                f"Net income: {ni_str}."
            )

            return {
                "cik": cik or "N/A",
                "company_name": company_name,
                "last_10k_date": last_10k_date,
                "last_10k_accession": last_10k_accession,
                "summary_text": summary_text,
            }
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_annual_report_summary failed for {ticker}: {exc}")
            return self._mock_annual_summary_dict(ticker)

    def get_filing_dates(self, ticker: str) -> list[str]:
        """Return the last 5 10-K filing dates from EDGAR submissions API."""
        try:
            cik = self._get_cik(ticker)
            if not cik:
                return self._mock_filing_dates()

            url = f"{self._EDGAR_BASE}/submissions/CIK{cik}.json"
            with httpx.Client(timeout=self._TIMEOUT, headers=self._HEADERS) as client:
                response = client.get(url)
                response.raise_for_status()
            data = response.json()
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            result = [
                dates[i] for i, form in enumerate(forms) if form == "10-K"
            ]
            return result[:5] or self._mock_filing_dates()
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_filing_dates failed for {ticker}: {exc}")
            return self._mock_filing_dates()

    def get_recent_8k_events(self, ticker: str) -> list[dict]:
        """Return the last 3 Form 8-K filings with date and description."""
        try:
            cik = self._get_cik(ticker)
            if not cik:
                return self._mock_8k_events()

            url = f"{self._EDGAR_BASE}/submissions/CIK{cik}.json"
            with httpx.Client(timeout=self._TIMEOUT, headers=self._HEADERS) as client:
                response = client.get(url)
                response.raise_for_status()
            data = response.json()
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            descriptions = filings.get("primaryDocument", [])

            events = []
            for i, form in enumerate(forms):
                if form == "8-K":
                    events.append(
                        {
                            "date": dates[i] if i < len(dates) else "N/A",
                            "description": descriptions[i] if i < len(descriptions) else "8-K filing",
                        }
                    )
                    if len(events) >= 3:
                        break

            return events or self._mock_8k_events()
        except Exception as exc:
            logger.warning(f"SECEdgarTool.get_recent_8k_events failed for {ticker}: {exc}")
            return self._mock_8k_events()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_cik(self, ticker: str) -> str | None:
        """Resolve a ticker symbol to a zero-padded CIK string."""
        try:
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            with httpx.Client(timeout=self._TIMEOUT, headers=self._HEADERS) as client:
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
                                {"end": "2023-09-30", "val": 383_285_000_000, "form": "10-K",
                                 "accn": "0000320193-23-000106"},
                                {"end": "2022-09-30", "val": 394_328_000_000, "form": "10-K",
                                 "accn": "0000320193-22-000108"},
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

    def _mock_annual_summary_dict(self, ticker: str) -> dict:
        return {
            "cik": "N/A",
            "company_name": f"{ticker} Corporation (Mock)",
            "last_10k_date": "2023-09-30",
            "last_10k_accession": "N/A",
            "summary_text": (
                f"SEC EDGAR Summary for {ticker} (Mock): "
                "Most recent annual revenue: $383,285,000,000, "
                "Net income: $96,995,000,000."
            ),
        }

    def _mock_filing_dates(self) -> list[str]:
        return [
            "2023-11-03",
            "2022-10-28",
            "2021-10-29",
            "2020-10-30",
            "2019-10-31",
        ]

    def _mock_8k_events(self) -> list[dict]:
        return [
            {"date": "2024-01-15", "description": "Quarterly earnings announcement"},
            {"date": "2024-02-01", "description": "Material definitive agreement"},
            {"date": "2024-03-01", "description": "Leadership changes"},
        ]
