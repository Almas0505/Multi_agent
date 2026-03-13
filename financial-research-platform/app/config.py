"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "FinancialResearchPlatform"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/financial_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # API Keys
    GROQ_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # File storage
    REPORTS_DIR: str = "./reports"
    CHARTS_DIR: str = "./charts"

    # Security / CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    AUTH_ENABLED: bool = False
    API_KEY: str = ""

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_ANALYSIS: str = "10/minute"
    RATE_LIMIT_STATUS: str = "60/minute"
    RATE_LIMIT_REPORTS: str = "120/minute"

    # Circuit breaker
    CIRCUIT_BREAKER_FAIL_MAX: int = 5
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 60

    # Cache TTLs (seconds)
    CACHE_TTL_ANALYSIS: int = 3600
    CACHE_TTL_PROGRESS: int = 86400
    CACHE_TTL_NEWS: int = 1800
    CACHE_TTL_TECHNICAL: int = 900


settings = Settings()
