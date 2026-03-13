"""Circuit breaker instances for external API calls."""

from __future__ import annotations

from loguru import logger

from app.config import settings


class _NoOpBreaker:
    """Pass-through stub used when pybreaker is not installed."""

    name: str = "noop"

    def call(self, func, *args, **kwargs):
        return func(*args, **kwargs)


try:
    import pybreaker  # type: ignore

    yfinance_breaker = pybreaker.CircuitBreaker(
        fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX,
        reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT,
        name="yfinance",
    )

    newsapi_breaker = pybreaker.CircuitBreaker(
        fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX,
        reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT,
        name="newsapi",
    )

    _PYBREAKER_AVAILABLE = True
    logger.info("Circuit breakers initialised (yfinance, newsapi)")

except ImportError:  # pragma: no cover
    yfinance_breaker = _NoOpBreaker()  # type: ignore[assignment]
    newsapi_breaker = _NoOpBreaker()  # type: ignore[assignment]
    _PYBREAKER_AVAILABLE = False
    logger.warning("pybreaker not installed – circuit breakers disabled")
