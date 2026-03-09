# 📊 Autonomous Financial Research Platform

> Multi-agent AI system that analyzes stocks like a Wall Street analyst.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  POST /api/v1/analyze/{ticker}  ──►  Celery Task Queue          │
│  GET  /api/v1/reports/{id}                                       │
│  WS   /ws/analysis/{task_id}                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   LangGraph Graph  │
                    │    init_node       │
                    └────────┬───────────┘
                             │  fan-out
          ┌──────────────────┼──────────────────────┐
          │          │       │       │               │
   ┌──────▼───┐ ┌────▼──┐ ┌─▼────┐ ┌▼──────────┐ ┌─▼────┐
   │Fundamentals│ │Sentiment│ │Tech │ │Competitor│ │Risk  │
   │  Agent   │ │ Agent │ │Agent│ │  Agent   │ │Agent │
   └──────┬───┘ └────┬──┘ └─┬────┘ └┬──────────┘ └─┬────┘
          └──────────┴───────┴───────┴───────────────┘
                             │  fan-in
                    ┌────────▼───────────┐
                    │  aggregator_node   │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │   report_node      │
                    │  (PDF generation)  │
                    └────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | Python 3.11, FastAPI, Uvicorn |
| Agent Orchestration | LangGraph, LangChain, Groq LLM |
| Financial Data | yFinance, SEC EDGAR, NewsAPI, FinnHub |
| Database | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Cache / Queue | Redis 7, Celery 5 |
| Vector Store | ChromaDB |
| PDF Reports | WeasyPrint, Jinja2 |
| Charts | Matplotlib |
| Containers | Docker, Docker Compose |

---

## Agents

| Agent | Responsibility |
|-------|---------------|
| **FundamentalsAgent** | P/E, P/B, EV/EBITDA, DCF valuation, SEC filing analysis |
| **SentimentAgent** | News sentiment scoring, insider transactions, analyst consensus |
| **TechnicalAgent** | RSI, MACD, Bollinger Bands, support/resistance, price chart |
| **CompetitorAgent** | Peer comparison, competitive position, economic moat analysis |
| **RiskAgent** | Beta, VaR(95%), max drawdown, debt analysis, regulatory risk scan |
| **ReportAgent** | Aggregates all data, writes executive summary, generates PDF |

All agents include **mock data fallbacks** so the platform runs without any API keys.

---

## Quick Start

### With Docker (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/financial-research-platform.git
cd financial-research-platform

# 2. Copy and edit the environment file
cp .env.example .env
# Edit .env and fill in your API keys (optional – mock data works without them)

# 3. Start all services
docker-compose up -d

# 4. Open the interactive API docs
open http://localhost:8080/docs
```

### Without Docker (local development)

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Run the API server (no DB/Redis required for basic operation)
uvicorn app.main:app --reload --port 8080
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analyze/{ticker}` | Start a new analysis |
| `GET` | `/api/v1/analyze/{task_id}/status` | Poll analysis progress |
| `GET` | `/api/v1/reports/` | List all reports (paginated) |
| `GET` | `/api/v1/reports/{id}` | Retrieve a single report |
| `GET` | `/api/v1/reports/{id}/download` | Download the PDF report |
| `DELETE` | `/api/v1/reports/{id}` | Delete a report |
| `WS` | `/ws/analysis/{task_id}` | Real-time progress via WebSocket |
| `GET` | `/health` | Health check |
| `GET` | `/` | Platform info |

### Example: start an analysis

```bash
curl -X POST http://localhost:8080/api/v1/analyze/AAPL
# → {"task_id": "...", "status": "queued", "message": "Analysis started for AAPL"}
```

### Example: check progress

```bash
curl http://localhost:8080/api/v1/analyze/<task_id>/status
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `FinancialResearchPlatform` |
| `DEBUG` | Enable debug mode | `false` |
| `VERSION` | Application version | `1.0.0` |
| `DATABASE_URL` | Async PostgreSQL URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/2` |
| `GROQ_API_KEY` | Groq LLM API key | *(empty – uses mock)* |
| `NEWS_API_KEY` | NewsAPI.org API key | *(empty – uses mock)* |
| `FINNHUB_API_KEY` | Finnhub API key | *(empty – uses mock)* |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | *(empty – uses mock)* |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8001` |
| `REPORTS_DIR` | PDF output directory | `./reports` |
| `CHARTS_DIR` | Chart image directory | `./charts` |

---

## Project Structure

```
financial-research-platform/
├── app/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # pydantic-settings configuration
│   ├── api/
│   │   ├── deps.py              # DB session & cache dependencies
│   │   └── routes/
│   │       ├── analysis.py      # Analysis endpoints
│   │       ├── reports.py       # Report CRUD endpoints
│   │       └── websocket.py     # Real-time WebSocket
│   ├── agents/
│   │   ├── orchestrator.py      # LangGraph workflow
│   │   ├── base.py              # Abstract BaseAgent
│   │   ├── fundamentals.py
│   │   ├── sentiment.py
│   │   ├── technical.py
│   │   ├── competitor.py
│   │   ├── risk.py
│   │   └── report.py
│   ├── tools/
│   │   ├── yfinance_tool.py
│   │   ├── news_tool.py
│   │   ├── sec_edgar_tool.py
│   │   ├── technical_indicators.py
│   │   └── competitor_tool.py
│   ├── models/
│   │   ├── state.py             # LangGraph TypedDict state
│   │   ├── schemas.py           # Pydantic API schemas
│   │   └── db_models.py         # SQLAlchemy ORM models
│   ├── services/
│   │   ├── cache.py             # Redis cache service
│   │   ├── celery_app.py        # Celery task definitions
│   │   ├── vector_store.py      # ChromaDB service
│   │   └── pdf_generator.py     # WeasyPrint PDF generation
│   └── db/
│       ├── base.py              # SQLAlchemy declarative base
│       ├── session.py           # Async engine & session factory
│       └── crud.py              # CRUD operations
├── alembic/                     # Database migrations
├── tests/                       # Pytest test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Database Migrations

```bash
# Apply migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"
```

---

## Disclaimer

This platform is for **informational and educational purposes only**. Nothing produced by this system constitutes financial or investment advice.
