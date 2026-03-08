"""ReportAgent – aggregates all agent outputs and generates the final report."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.models.state import FinancialResearchState


class ReportAgent(BaseAgent):
    """Agent that writes an executive summary and triggers PDF generation."""

    def __init__(self, llm=None) -> None:
        super().__init__(llm=llm)

    async def run(self, state: FinancialResearchState) -> dict:
        """Generate the final analytical report and optional PDF."""
        ticker = state["ticker"]
        self.logger.info(f"ReportAgent starting for {ticker}")

        try:
            fund = state.get("fundamentals_data") or {}
            sent = state.get("sentiment_data") or {}
            tech = state.get("technical_data") or {}
            comp = state.get("competitor_data") or {}
            risk = state.get("risk_data") or {}

            rating = self._determine_final_rating(fund, sent, tech, risk)
            target_price = self._estimate_target_price(fund, tech)

            prompt = (
                f"You are a senior Wall Street analyst. Write an executive summary for {ticker}.\n\n"
                f"FUNDAMENTALS: Rating={fund.get('rating')}, P/E={fund.get('pe_ratio')}, "
                f"DCF Fair Value=${fund.get('dcf_fair_value')}, Net Margin={fund.get('net_margin')}\n"
                f"SENTIMENT: Score={sent.get('sentiment_score')}/10, "
                f"News={sent.get('news_sentiment')}\n"
                f"TECHNICAL: Trend={tech.get('trend')}, RSI={tech.get('rsi')}\n"
                f"COMPETITOR: Position={comp.get('competitive_position')}\n"
                f"RISK: Score={risk.get('risk_score')}/10, Level={risk.get('risk_level')}\n\n"
                f"Overall rating: {rating}, Target Price: ${target_price:.2f}\n\n"
                f"Write a 3-paragraph executive summary suitable for an institutional investor."
            )
            final_analysis = await self._invoke_llm(
                prompt,
                fallback=self._mock_executive_summary(ticker, rating, target_price, fund, sent, tech, risk),
            )

            # Generate PDF if the service is available
            pdf_path = await self._generate_pdf(state, final_analysis)

            return {
                "final_analysis": final_analysis,
                "pdf_path": pdf_path,
                "status": "completed",
                "completed_agents": state.get("completed_agents", []) + ["report"],
            }
        except Exception as exc:
            self.logger.error(f"ReportAgent failed for {ticker}: {exc}")
            return {
                "final_analysis": f"Report generation failed for {ticker}: {exc}",
                "errors": state.get("errors", []) + [f"ReportAgent: {exc}"],
                "status": "failed",
                "completed_agents": state.get("completed_agents", []) + ["report"],
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _determine_final_rating(self, fund: dict, sent: dict, tech: dict, risk: dict) -> str:
        """Vote across agents to determine final BUY/HOLD/SELL rating."""
        votes = {"BUY": 0, "HOLD": 0, "SELL": 0}

        # Fundamentals vote
        fund_rating = fund.get("rating", "HOLD")
        votes[fund_rating] = votes.get(fund_rating, 0) + 2  # weight 2

        # Sentiment vote
        score = sent.get("sentiment_score", 5)
        votes["BUY" if score >= 6.5 else ("SELL" if score <= 3.5 else "HOLD")] += 1

        # Technical vote
        trend = tech.get("trend", "NEUTRAL")
        votes["BUY" if trend == "BULLISH" else ("SELL" if trend == "BEARISH" else "HOLD")] += 1

        # Risk penalty
        risk_level = risk.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            votes["SELL"] += 1

        return max(votes, key=lambda k: votes[k])

    def _estimate_target_price(self, fund: dict, tech: dict) -> float:
        dcf = fund.get("dcf_fair_value") or 195.0
        resistance = (tech.get("resistance_levels") or [dcf])[0]
        return round((dcf + resistance) / 2, 2)

    async def _generate_pdf(self, state: FinancialResearchState, final_analysis: str) -> str | None:
        """Attempt to generate a PDF report; return path or None on failure."""
        try:
            from app.services.pdf_generator import PDFGenerator
            from app.config import settings
            from pathlib import Path

            output_dir = Path(settings.REPORTS_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{state['ticker']}_report.pdf")

            # Inject final_analysis into state copy for the generator
            state_copy = dict(state)
            state_copy["final_analysis"] = final_analysis

            generator = PDFGenerator()
            return generator.generate_report(state_copy, output_path)  # type: ignore[arg-type]
        except Exception as exc:
            self.logger.warning(f"PDF generation skipped: {exc}")
            return None

    def _mock_executive_summary(
        self,
        ticker: str,
        rating: str,
        target_price: float,
        fund: dict,
        sent: dict,
        tech: dict,
        risk: dict,
    ) -> str:
        return (
            f"**{ticker} – Executive Summary | Rating: {rating} | Target: ${target_price:.2f}**\n\n"
            f"{ticker} presents a compelling investment case driven by strong fundamentals "
            f"(P/E: {fund.get('pe_ratio', 'N/A')}, DCF Fair Value: ${fund.get('dcf_fair_value', 'N/A')}) "
            f"and positive market sentiment (score: {sent.get('sentiment_score', 'N/A')}/10). "
            f"The technical picture confirms a {tech.get('trend', 'NEUTRAL')} trend with "
            f"key support levels intact.\n\n"
            f"Risk assessment yields a score of {risk.get('risk_score', 'N/A')}/10 "
            f"({risk.get('risk_level', 'MEDIUM')} risk), which is manageable for long-term investors. "
            f"The company maintains competitive advantages that support durable earnings power.\n\n"
            f"**Conclusion:** We rate {ticker} a **{rating}** with a 12-month price target of "
            f"${target_price:.2f}, representing meaningful upside from current levels."
        )
