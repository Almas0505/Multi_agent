"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.middleware.auth import verify_api_key
from app.api.middleware.rate_limiter import _SLOWAPI_AVAILABLE, limiter
from app.api.routes import analysis, reports, websocket
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info("All services initialized successfully")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title="Autonomous Financial Research Platform",
    description="Multi-agent AI system that analyzes stocks like a Wall Street analyst.",
    version=settings.VERSION,
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS – restrict origins in production via ALLOWED_ORIGINS env var
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Rate limiting (slowapi)
# ------------------------------------------------------------------
if _SLOWAPI_AVAILABLE:
    from slowapi import _rate_limit_exceeded_handler  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------------------------------------------
# Global validation error handler – consistent JSON error format
# ------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": "VALIDATION_ERROR", "message": str(exc), "agent": None},
    )

# ------------------------------------------------------------------
# Routers – protected by API key when AUTH_ENABLED=True
# ------------------------------------------------------------------
_auth_dep = [Depends(verify_api_key)]

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"], dependencies=_auth_dep)
app.include_router(reports.router, prefix="/api/v1", tags=["reports"], dependencies=_auth_dep)
app.include_router(websocket.router, tags=["websocket"])  # WebSocket auth handled separately


@app.get("/health", response_model=dict)
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}


@app.get("/")
async def root() -> dict:
    """Root endpoint with project information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": "Multi-agent AI system that analyzes stocks like a Wall Street analyst.",
        "docs": "/docs",
        "health": "/health",
    }
