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
            composite_score = self._compute_composite_score(fund, sent, tech, risk, comp)
            key_risks = self._extract_key_risks(risk, fund)
            key_catalysts = self._extract_key_catalysts(fund, sent, tech)

            prompt = (
                f"You are a senior Wall Street analyst. Write an executive summary for {ticker}.\n\n"
                f"FUNDAMENTALS: Rating={fund.get('rating')}, P/E={fund.get('pe_ratio')}, "
                f"DCF Fair Value=${fund.get('dcf_fair_value')}, Net Margin={fund.get('net_margin')}, "
                f"Revenue Trend={fund.get('revenue_trend')}\n"
                f"SENTIMENT: Score={sent.get('sentiment_score')}/10, "
                f"Label={sent.get('sentiment_label')}, News={sent.get('news_sentiment')}\n"
                f"TECHNICAL: Trend={tech.get('trend_signal') or tech.get('trend')}, "
                f"RSI={tech.get('rsi')}, Support={tech.get('support')}, "
                f"Resistance={tech.get('resistance')}\n"
                f"COMPETITOR: Position={comp.get('competitive_position')}, "
                f"Moat={comp.get('moat_analysis', '')[:100]}\n"
                f"RISK: Level={risk.get('risk_level')}, Beta={risk.get('beta')}, "
                f"VaR={risk.get('var_95')}, Volatility={risk.get('volatility')}\n\n"
                f"Overall rating: {rating}, Target Price: ${target_price:.2f}, "
                f"Composite Score: {composite_score}/100\n\n"
                f"Key Risks: {'; '.join(key_risks[:3])}\n"
                f"Key Catalysts: {'; '.join(key_catalysts[:3])}\n\n"
                f"Write a 3-paragraph executive summary suitable for an institutional investor."
            )
            final_analysis = await self._invoke_llm(
                prompt,
                fallback=self._mock_executive_summary(
                    ticker, rating, target_price, fund, sent, tech, risk, composite_score
                ),
            )

            # Generate PDF if the service is available
            pdf_path = await self._generate_pdf(state, final_analysis)

            return {
                "final_analysis": final_analysis,
                "pdf_path": pdf_path,
                "status": "completed",
                "composite_score": composite_score,
                "key_risks": key_risks,
                "key_catalysts": key_catalysts,
                "final_rating": rating,
                "target_price": target_price,
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

        # Fundamentals vote (weight 2)
        fund_rating = fund.get("rating", "HOLD")
        votes[fund_rating] = votes.get(fund_rating, 0) + 2

        # Sentiment vote
        score = sent.get("sentiment_score", 5)
        votes["BUY" if score >= 6.5 else ("SELL" if score <= 3.5 else "HOLD")] += 1

        # Technical vote (use trend_signal if available)
        trend = tech.get("trend_signal") or tech.get("trend", "NEUTRAL")
        votes["BUY" if trend == "BULLISH" else ("SELL" if trend == "BEARISH" else "HOLD")] += 1

        # Risk penalty
        risk_level = risk.get("risk_level", "MEDIUM")
        if risk_level == "HIGH":
            votes["SELL"] += 1

        return max(votes, key=lambda k: votes[k])

    def _estimate_target_price(self, fund: dict, tech: dict) -> float:
        dcf = fund.get("dcf_fair_value") or 195.0
        resistance = tech.get("resistance") or (tech.get("resistance_levels") or [dcf])[0]
        return round((dcf + resistance) / 2, 2)

    def _compute_composite_score(
        self, fund: dict, sent: dict, tech: dict, risk: dict, comp: dict
    ) -> float:
        """Weighted composite score 0-100.

        Weights reflect relative importance of each analysis dimension:
        - Fundamentals (30%): primary driver of intrinsic value
        - Technical (25%): short-to-medium term price momentum
        - Sentiment (20%): market perception and news flow
        - Risk (15%): risk-adjusted return consideration
        - Competitor (10%): relative competitive positioning
        BUY=100, HOLD=50, SELL=0 for each component.
        """
        rating_to_score = {"BUY": 100.0, "HOLD": 50.0, "SELL": 0.0}

        fund_score = rating_to_score.get(fund.get("rating", "HOLD"), 50.0)

        trend = tech.get("trend_signal") or tech.get("trend", "NEUTRAL")
        tech_rating = "BUY" if trend == "BULLISH" else ("SELL" if trend == "BEARISH" else "HOLD")
        tech_score = rating_to_score.get(tech_rating, 50.0)

        sent_label = sent.get("sentiment_label", "NEUTRAL")
        sent_rating = "BUY" if sent_label == "BULLISH" else ("SELL" if sent_label == "BEARISH" else "HOLD")
        sent_score = rating_to_score.get(sent_rating, 50.0)

        risk_level = risk.get("risk_level", "MEDIUM")
        # For risk: LOW risk = BUY score, HIGH risk = SELL score
        risk_score = {"LOW": 100.0, "MEDIUM": 50.0, "HIGH": 0.0}.get(risk_level, 50.0)

        comp_rating = comp.get("rating", "HOLD")
        comp_score = rating_to_score.get(comp_rating, 50.0)

        composite = (
            fund_score * 0.30
            + tech_score * 0.25
            + sent_score * 0.20
            + risk_score * 0.15
            + comp_score * 0.10
        )
        return round(composite, 1)

    def _extract_key_risks(self, risk: dict, fund: dict) -> list[str]:
        risks: list[str] = []
        key_risks = risk.get("key_risks", [])
        risks.extend(key_risks[:3])
        if fund.get("debt_equity", 0) and (fund.get("debt_equity") or 0) > 2:
            risks.append(f"High leverage: D/E ratio of {fund.get('debt_equity'):.1f}x.")
        return risks[:5]

    def _extract_key_catalysts(self, fund: dict, sent: dict, tech: dict) -> list[str]:
        catalysts: list[str] = []
        if (fund.get("revenue_growth") or 0) > 0.10:
            catalysts.append(f"Strong revenue growth of {fund.get('revenue_growth'):.1%} YoY.")
        top_positive = sent.get("top_positive_headline", "")
        if top_positive:
            catalysts.append(f"Positive news: {top_positive[:80]}")
        trend = tech.get("trend_signal") or tech.get("trend", "NEUTRAL")
        if trend == "BULLISH":
            catalysts.append("Bullish technical trend with price above key moving averages.")
        if not catalysts:
            catalysts.append("Stable business fundamentals support long-term value creation.")
        return catalysts[:5]

    async def _generate_pdf(self, state: FinancialResearchState, final_analysis: str) -> str | None:
        """Attempt to generate a PDF report; return path or None on failure."""
        try:
            from app.services.pdf_generator import PDFGenerator
            from app.config import settings
            from pathlib import Path

            output_dir = Path(settings.REPORTS_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{state['ticker']}_report.pdf")

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
        composite_score: float = 50.0,
    ) -> str:
        return (
            f"**{ticker} – Executive Summary | Rating: {rating} | Target: ${target_price:.2f} | "
            f"Composite Score: {composite_score}/100**\n\n"
            f"{ticker} presents a compelling investment case driven by strong fundamentals "
            f"(P/E: {fund.get('pe_ratio', 'N/A')}, DCF Fair Value: ${fund.get('dcf_fair_value', 'N/A')}) "
            f"and positive market sentiment (score: {sent.get('sentiment_score', 'N/A')}/10, "
            f"label: {sent.get('sentiment_label', 'N/A')}). "
            f"The technical picture confirms a {tech.get('trend_signal') or tech.get('trend', 'NEUTRAL')} trend "
            f"with key support levels intact.\n\n"
            f"Risk assessment yields a level of {risk.get('risk_level', 'MEDIUM')} "
            f"(Beta: {risk.get('beta', 'N/A')}, VaR: {risk.get('var_95', 'N/A')}), "
            f"which is manageable for long-term investors. "
            f"The company maintains competitive advantages that support durable earnings power.\n\n"
            f"**Conclusion:** We rate {ticker} a **{rating}** with a 12-month price target of "
            f"${target_price:.2f}, representing meaningful upside from current levels."
        )
