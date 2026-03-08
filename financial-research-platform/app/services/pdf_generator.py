"""PDF report generator using Jinja2 + WeasyPrint."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, BaseLoader
from loguru import logger

from app.models.state import FinancialResearchState

try:
    import weasyprint  # type: ignore
    _WEASYPRINT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _WEASYPRINT_AVAILABLE = False

# ---------------------------------------------------------------------------
# HTML / CSS template
# ---------------------------------------------------------------------------

_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>{{ ticker }} Financial Analysis Report</title>
  <style>
    body { font-family: Arial, sans-serif; font-size: 12px; color: #222; margin: 40px; }
    h1 { color: #1a237e; border-bottom: 2px solid #1a237e; padding-bottom: 8px; }
    h2 { color: #283593; margin-top: 24px; }
    h3 { color: #3949ab; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold;
             color: #fff; font-size: 14px; }
    .buy  { background: #2e7d32; }
    .hold { background: #f57f17; }
    .sell { background: #c62828; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
    th { background: #e8eaf6; font-weight: bold; }
    .section { margin-bottom: 24px; page-break-inside: avoid; }
    .metric { margin: 4px 0; }
    pre { white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px; }
    footer { text-align: center; font-size: 10px; color: #888; margin-top: 40px; }
  </style>
</head>
<body>
  <h1>📊 {{ ticker }} – Autonomous Financial Research Report</h1>
  <p><strong>Company:</strong> {{ company_name }} &nbsp;|&nbsp;
     <strong>Sector:</strong> {{ sector }} &nbsp;|&nbsp;
     <strong>Date:</strong> {{ created_at }}</p>

  {% if final_rating %}
  <p>Overall Rating: <span class="badge {{ final_rating | lower }}">{{ final_rating }}</span></p>
  {% endif %}

  <!-- EXECUTIVE SUMMARY -->
  <div class="section">
    <h2>Executive Summary</h2>
    <pre>{{ final_analysis }}</pre>
  </div>

  <!-- FUNDAMENTALS -->
  {% if fundamentals_data %}
  <div class="section">
    <h2>Fundamentals</h2>
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>P/E Ratio</td><td>{{ fundamentals_data.pe_ratio }}</td></tr>
      <tr><td>P/B Ratio</td><td>{{ fundamentals_data.pb_ratio }}</td></tr>
      <tr><td>EV/EBITDA</td><td>{{ fundamentals_data.ev_ebitda }}</td></tr>
      <tr><td>Net Margin</td><td>{{ fundamentals_data.net_margin }}</td></tr>
      <tr><td>ROE</td><td>{{ fundamentals_data.roe }}</td></tr>
      <tr><td>D/E Ratio</td><td>{{ fundamentals_data.debt_equity }}</td></tr>
      <tr><td>Revenue Growth</td><td>{{ fundamentals_data.revenue_growth }}</td></tr>
      <tr><td>DCF Fair Value</td><td>${{ fundamentals_data.dcf_fair_value }}</td></tr>
      <tr><td>Rating</td><td><strong>{{ fundamentals_data.rating }}</strong></td></tr>
    </table>
    <pre>{{ fundamentals_data.analysis_text }}</pre>
  </div>
  {% endif %}

  <!-- SENTIMENT -->
  {% if sentiment_data %}
  <div class="section">
    <h2>Sentiment Analysis</h2>
    <p>Sentiment Score: <strong>{{ sentiment_data.sentiment_score }}/10</strong>
       ({{ sentiment_data.news_sentiment }})</p>
    <pre>{{ sentiment_data.analysis_text }}</pre>
  </div>
  {% endif %}

  <!-- TECHNICAL -->
  {% if technical_data %}
  <div class="section">
    <h2>Technical Analysis</h2>
    <table>
      <tr><th>Indicator</th><th>Value</th></tr>
      <tr><td>Trend</td><td>{{ technical_data.trend }}</td></tr>
      <tr><td>RSI</td><td>{{ technical_data.rsi }}</td></tr>
      <tr><td>MACD Signal</td><td>{{ technical_data.macd_signal }}</td></tr>
      <tr><td>SMA 50</td><td>{{ technical_data.sma_50 }}</td></tr>
      <tr><td>SMA 200</td><td>{{ technical_data.sma_200 }}</td></tr>
      <tr><td>Bollinger Position</td><td>{{ technical_data.bollinger_position }}</td></tr>
    </table>
    <pre>{{ technical_data.analysis_text }}</pre>
  </div>
  {% endif %}

  <!-- COMPETITOR -->
  {% if competitor_data %}
  <div class="section">
    <h2>Competitive Analysis</h2>
    <p>Position: <strong>{{ competitor_data.competitive_position }}</strong></p>
    <pre>{{ competitor_data.analysis_text }}</pre>
  </div>
  {% endif %}

  <!-- RISK -->
  {% if risk_data %}
  <div class="section">
    <h2>Risk Assessment</h2>
    <table>
      <tr><th>Metric</th><th>Value</th></tr>
      <tr><td>Risk Score</td><td>{{ risk_data.risk_score }}/10</td></tr>
      <tr><td>Risk Level</td><td>{{ risk_data.risk_level }}</td></tr>
      <tr><td>Beta</td><td>{{ risk_data.beta }}</td></tr>
      <tr><td>VaR (95%)</td><td>{{ "%.2f%%" | format(risk_data.var_95 * 100) }}</td></tr>
      <tr><td>Max Drawdown</td><td>{{ "%.2f%%" | format(risk_data.max_drawdown * 100) }}</td></tr>
    </table>
    {% if risk_data.key_risks %}
    <h3>Key Risks</h3>
    <ul>{% for risk in risk_data.key_risks %}<li>{{ risk }}</li>{% endfor %}</ul>
    {% endif %}
  </div>
  {% endif %}

  <footer>
    Generated by Autonomous Financial Research Platform &mdash; For informational purposes only.
    This is not investment advice.
  </footer>
</body>
</html>
"""


class PDFGenerator:
    """Render an HTML report from state data and convert to PDF via WeasyPrint."""

    def __init__(self) -> None:
        self._env = Environment(loader=BaseLoader())

    def generate_report(self, state: FinancialResearchState, output_path: str) -> str:
        """Render the report and write to *output_path*; returns the path."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Determine final rating from fundamentals or report agent
        final_rating = (
            (state.get("fundamentals_data") or {}).get("rating")
            or "HOLD"
        )

        context = {
            "ticker": state.get("ticker", "N/A"),
            "company_name": state.get("company_name", "N/A"),
            "sector": state.get("sector", "N/A"),
            "created_at": state.get("created_at", "N/A"),
            "final_analysis": state.get("final_analysis", ""),
            "final_rating": final_rating,
            "fundamentals_data": state.get("fundamentals_data"),
            "sentiment_data": state.get("sentiment_data"),
            "technical_data": state.get("technical_data"),
            "competitor_data": state.get("competitor_data"),
            "risk_data": state.get("risk_data"),
        }

        template = self._env.from_string(_REPORT_TEMPLATE)
        html_content = template.render(**context)

        if _WEASYPRINT_AVAILABLE:
            try:
                weasyprint.HTML(string=html_content).write_pdf(output_path)
                logger.info(f"PDF report saved to {output_path}")
                return output_path
            except Exception as exc:
                logger.error(f"WeasyPrint PDF generation failed: {exc}")

        # Fallback: save as HTML
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html_content)
        logger.info(f"HTML report (WeasyPrint fallback) saved to {html_path}")
        return html_path
