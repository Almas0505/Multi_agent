"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(websocket.router, tags=["websocket"])


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
