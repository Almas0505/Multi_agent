"""LangGraph state definition for financial research workflow."""

from typing import Optional, TypedDict


class FinancialResearchState(TypedDict):
    """State shared across all agents in the LangGraph workflow."""

    ticker: str
    company_name: str
    sector: str
    price_data: Optional[dict]
    financial_statements: Optional[dict]
    fundamentals_data: Optional[dict]
    sentiment_data: Optional[dict]
    technical_data: Optional[dict]
    competitor_data: Optional[dict]
    risk_data: Optional[dict]
    final_analysis: Optional[str]
    pdf_path: Optional[str]
    report_id: Optional[str]
    errors: list[str]
    completed_agents: list[str]
    status: str
    created_at: str
