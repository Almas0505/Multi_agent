"""SQLAlchemy ORM database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Report(Base):
    """ORM model representing a financial analysis report."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )  # queued | running | completed | failed

    fundamentals_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sentiment_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    technical_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    competitor_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
