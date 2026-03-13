"""Unified error schema for agent and API errors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error detail returned by agents and API routes."""

    code: str
    message: str
    agent: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def make_agent_error(agent_name: str, exc: Exception) -> dict:
    """Return a serialisable ErrorDetail dict for an agent exception."""
    return ErrorDetail(
        code="AGENT_ERROR",
        message=str(exc),
        agent=agent_name,
    ).model_dump()
