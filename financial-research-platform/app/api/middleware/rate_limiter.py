"""Shared slowapi rate limiter instance."""

from __future__ import annotations

try:
    from slowapi import Limiter  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore

    limiter = Limiter(key_func=get_remote_address)
    _SLOWAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    limiter = None  # type: ignore[assignment]
    _SLOWAPI_AVAILABLE = False
