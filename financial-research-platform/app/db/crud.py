"""CRUD operations for the Report model."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Report


async def create_report(db: AsyncSession, ticker: str) -> Report:
    """Create a new report record with status 'queued'."""
    report = Report(
        id=uuid.uuid4(),
        ticker=ticker.upper(),
        status="queued",
        errors=[],
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


async def get_report(db: AsyncSession, report_id: str) -> Optional[Report]:
    """Retrieve a single report by its ID."""
    result = await db.execute(select(Report).where(Report.id == uuid.UUID(report_id)))
    return result.scalar_one_or_none()


async def get_reports(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[Report]:
    """Retrieve a paginated list of reports ordered by creation date."""
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_report(db: AsyncSession, report_id: str, data: dict) -> Optional[Report]:
    """Update report fields and persist the changes."""
    report = await get_report(db, report_id)
    if report is None:
        return None
    for key, value in data.items():
        setattr(report, key, value)
    await db.flush()
    await db.refresh(report)
    return report


async def delete_report(db: AsyncSession, report_id: str) -> bool:
    """Delete a report. Returns True when successful, False when not found."""
    report = await get_report(db, report_id)
    if report is None:
        return False
    await db.delete(report)
    await db.flush()
    return True
