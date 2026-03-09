"""Analysis routes – start a new analysis and check task progress."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_cache, get_db
from app.db import crud
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.services.cache import CacheService

router = APIRouter()

_VALID_TICKER_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")


def _validate_ticker(ticker: str) -> str:
    """Normalise and validate a ticker symbol. Raises HTTPException on failure."""
    cleaned = ticker.strip().upper()
    if not cleaned or len(cleaned) > 10:
        raise HTTPException(status_code=422, detail=f"Invalid ticker symbol: '{ticker}'")
    if not all(c in _VALID_TICKER_CHARS for c in cleaned):
        raise HTTPException(status_code=422, detail=f"Ticker contains invalid characters: '{ticker}'")
    return cleaned


@router.post("/analyze/{ticker}", response_model=AnalysisResponse)
async def start_analysis(
    ticker: str,
    request: AnalysisRequest | None = None,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
) -> AnalysisResponse:
    """Submit a financial analysis task for *ticker*.

    Returns a *task_id* that can be used to track progress.
    """
    validated_ticker = _validate_ticker(ticker)

    # Use request body fields if provided, else sensible defaults
    include_pdf = (request.include_pdf if request else True)

    # Check recent cache hit
    cached = await cache.get(f"analysis:{validated_ticker}")
    if cached:
        logger.info(f"Returning cached analysis for {validated_ticker}")
        return AnalysisResponse(
            task_id=cached["report_id"],
            status="completed",
            message=f"Returning cached result for {validated_ticker}",
        )

    # Create a DB record
    try:
        report = await crud.create_report(db, validated_ticker)
        report_id = str(report.id)
    except Exception as exc:
        logger.error(f"Failed to create report record: {exc}")
        # Fall back to an in-memory ID when DB is unavailable
        report_id = str(uuid.uuid4())

    # Dispatch Celery task (or run inline if Celery is unavailable)
    try:
        from app.services.celery_app import run_financial_analysis, _CELERY_AVAILABLE

        if _CELERY_AVAILABLE:
            run_financial_analysis.delay(validated_ticker, report_id, include_pdf)
            logger.info(f"Celery task dispatched for {validated_ticker} (id={report_id})")
        else:
            import asyncio
            asyncio.create_task(run_financial_analysis(validated_ticker, report_id, include_pdf))
            logger.info(f"Async task created for {validated_ticker} (id={report_id})")
    except Exception as exc:
        logger.error(f"Failed to dispatch task for {validated_ticker}: {exc}")

    # Seed initial progress
    await cache.set_progress(
        report_id,
        {"agent": "init", "progress": 0, "status": "queued", "message": "Analysis queued"},
    )

    return AnalysisResponse(
        task_id=report_id,
        status="queued",
        message=f"Analysis started for {validated_ticker}",
    )


@router.get("/analyze/{task_id}/status")
async def get_analysis_status(
    task_id: str,
    cache: CacheService = Depends(get_cache),
) -> dict:
    """Return the current progress of an analysis task."""
    progress = await cache.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return progress
