"""Reports routes – list, get, download, and delete analysis reports."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.middleware.rate_limiter import _SLOWAPI_AVAILABLE, limiter
from app.config import settings
from app.db import crud
from app.models.schemas import ReportResponse

router = APIRouter()


def _rate_limit(limit_str: str):
    """Return a slowapi limit decorator or a no-op if slowapi is unavailable."""
    if _SLOWAPI_AVAILABLE:
        return limiter.limit(limit_str)
    def _noop(fn):
        return fn
    return _noop


def _report_to_response(report) -> ReportResponse:
    return ReportResponse(
        id=str(report.id),
        ticker=report.ticker,
        status=report.status,
        created_at=report.created_at,
        pdf_url=f"/api/v1/reports/{report.id}/download" if report.pdf_path else None,
        data={
            "fundamentals": report.fundamentals_data,
            "sentiment": report.sentiment_data,
            "technical": report.technical_data,
            "competitor": report.competitor_data,
            "risk": report.risk_data,
            "final_analysis": report.final_analysis,
        },
        errors=report.errors or [],
    )


@router.get("/reports/", response_model=list[ReportResponse])
@_rate_limit(settings.RATE_LIMIT_REPORTS)
async def list_reports(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[ReportResponse]:
    """Return a paginated list of analysis reports."""
    reports = await crud.get_reports(db, skip=skip, limit=limit)
    return [_report_to_response(r) for r in reports]


@router.get("/reports/{report_id}", response_model=ReportResponse)
@_rate_limit(settings.RATE_LIMIT_REPORTS)
async def get_report(
    request: Request,
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Return a single report by ID."""
    report = await crud.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return _report_to_response(report)


@router.get("/reports/{report_id}/download")
@_rate_limit(settings.RATE_LIMIT_REPORTS)
async def download_report(
    request: Request,
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream the PDF file for the given report."""
    report = await crud.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    if not report.pdf_path or not Path(report.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not yet available for this report.")
    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=f"{report.ticker}_report.pdf",
    )


@router.delete("/reports/{report_id}", status_code=200)
@_rate_limit(settings.RATE_LIMIT_REPORTS)
async def delete_report(
    request: Request,
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a report and its associated PDF file."""
    report = await crud.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    # Remove PDF file if present
    if report.pdf_path and Path(report.pdf_path).exists():
        try:
            os.remove(report.pdf_path)
        except OSError:
            pass

    await crud.delete_report(db, report_id)
    return {"detail": f"Report '{report_id}' deleted."}
