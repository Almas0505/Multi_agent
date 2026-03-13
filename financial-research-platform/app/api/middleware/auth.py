"""API key authentication dependency."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config import settings


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    """Validate the X-API-Key header when AUTH_ENABLED is True.

    Raises HTTP 401 if the key is missing or incorrect.
    Skips validation entirely when AUTH_ENABLED=False (default for dev/test).
    """
    if not settings.AUTH_ENABLED:
        return
    if not settings.API_KEY or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or missing API key"},
        )
