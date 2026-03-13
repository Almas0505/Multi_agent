"""Celery application and financial analysis task definition."""

from __future__ import annotations

from loguru import logger

try:
    from celery import Celery  # type: ignore
    _CELERY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CELERY_AVAILABLE = False

from app.config import settings

if _CELERY_AVAILABLE:
    celery_app = Celery(
        "financial_research",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
else:
    celery_app = None  # type: ignore[assignment]


def _run_financial_analysis_sync(ticker: str, report_id: str, include_pdf: bool) -> dict:
    """Synchronous wrapper executed inside the Celery worker process."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        _run_financial_analysis_async(ticker, report_id, include_pdf)
    )


async def _run_financial_analysis_async(ticker: str, report_id: str, include_pdf: bool) -> dict:
    """Async implementation of the full financial analysis pipeline."""
    from app.agents.orchestrator import financial_graph
    from app.models.state import FinancialResearchState
    from app.services.cache import CacheService

    cache = CacheService()

    async def _update_progress(agent: str, progress: int, message: str, status: str = "running") -> None:
        await cache.set_progress(
            report_id,
            {"agent": agent, "progress": progress, "status": status, "message": message},
        )

    await _update_progress("init", 5, "Starting financial analysis…")

    initial_state: FinancialResearchState = {  # type: ignore[typeddict-item]
        "ticker": ticker,
        "company_name": "",
        "sector": "",
        "price_data": None,
        "financial_statements": None,
        "fundamentals_data": None,
        "sentiment_data": None,
        "technical_data": None,
        "competitor_data": None,
        "risk_data": None,
        "final_analysis": None,
        "pdf_path": None,
        "report_id": report_id,
        "errors": [],
        "completed_agents": [],
        "status": "running",
        "created_at": "",
    }

    try:
        await _update_progress("orchestrator", 10, "Running agent graph…")
        final_state = await financial_graph.ainvoke(initial_state)
    except AttributeError:
        # Fallback when graph is a plain coroutine function
        final_state = await financial_graph(initial_state)

    # Signal completion — WebSocket will close on this status
    await _update_progress("complete", 100, "Analysis complete.", status="completed")

    # Persist results to database
    try:
        from app.db.session import get_session
        from app.db import crud

        async with get_session() as db:
            await crud.update_report(
                db,
                report_id,
                {
                    "status": final_state.get("status", "completed"),
                    "fundamentals_data": final_state.get("fundamentals_data"),
                    "sentiment_data": final_state.get("sentiment_data"),
                    "technical_data": final_state.get("technical_data"),
                    "competitor_data": final_state.get("competitor_data"),
                    "risk_data": final_state.get("risk_data"),
                    "final_analysis": final_state.get("final_analysis"),
                    "pdf_path": final_state.get("pdf_path"),
                    "errors": final_state.get("errors", []),
                },
            )
    except Exception as exc:
        logger.error(f"Failed to persist results for {report_id}: {exc}")

    return dict(final_state)


if _CELERY_AVAILABLE:
    @celery_app.task(name="run_financial_analysis", bind=True)
    def run_financial_analysis(self, ticker: str, report_id: str, include_pdf: bool = True) -> dict:
        """Celery task: run the full financial analysis pipeline."""
        logger.info(f"Starting Celery task for {ticker} (report_id={report_id})")
        return _run_financial_analysis_sync(ticker, report_id, include_pdf)
else:
    async def run_financial_analysis(ticker: str, report_id: str, include_pdf: bool = True) -> dict:  # type: ignore[misc]
        """Async fallback when Celery is not installed."""
        return await _run_financial_analysis_async(ticker, report_id, include_pdf)
