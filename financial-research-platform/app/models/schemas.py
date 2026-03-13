"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request model for starting a financial analysis."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")
    include_pdf: bool = Field(True, description="Whether to generate a PDF report")


class AnalysisResponse(BaseModel):
    """Response model returned when an analysis task is submitted."""

    task_id: str
    status: str
    message: str


class ReportResponse(BaseModel):
    """Response model for a completed or in-progress analysis report."""

    id: str
    ticker: str
    status: str
    created_at: datetime
    pdf_url: Optional[str] = None
    data: Optional[dict] = None
    errors: list[Any] = []


class WebSocketMessage(BaseModel):
    """Message format sent over the WebSocket connection."""

    agent: str
    status: str
    progress: int = Field(..., ge=0, le=100)
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
