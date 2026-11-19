# DuesWise Backend (Developer A)

Phase 1 + Phase 2: FastAPI application, SQLite/SQLAlchemy database setup,
environment-based configuration, health/system-status endpoints, centralised
error handling, and transaction data foundation (ingestion, parsing,
categorisation, deduplication, transaction API).

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic v2
- pytest + httpx
- python-multipart (file uploads)
- pdfplumber (PDF text extraction)

## Install dependencies

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# or: source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## Initialise the database

Database tables are created automatically on application startup via
`init_db()`. To initialise manually:

```bash
python -c "from app.database import init_db; init_db()"
```

## Run the server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Endpoints

### Health & system
- `GET /health` — health check
- `GET /api/v1/system/status` — system information

### Authentication (demo session, CONTRACT.md §3)
- `POST /api/v1/auth/demo` — create demo session (persona: salaried/young_professional/shopkeeper)
- `GET /api/v1/auth/me` — get current user (requires Bearer token)

### Transactions (CONTRACT.md §5)
- `GET /api/v1/transactions` — list transactions (paginated, filtered)
- `GET /api/v1/transactions/{transaction_id}` — get a transaction
- `POST /api/v1/transactions/manual` — create a manual transaction

### Transaction ingestion (CONTRACT.md §6)
- `POST /api/v1/transactions/ingest/sms` — parse and ingest one SMS
- `POST /api/v1/transactions/ingest/file` — upload CSV/PDF statement (multipart)
- `POST /api/v1/transactions/ingest/aa-mock` — synthetic Account Aggregator ingestion

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
copy .env.example .env        # Windows
# or: cp .env.example .env    # macOS/Linux
```

## Run tests

```bash
cd backend
pytest -v
```

## Ownership

Developer A owns `backend/**`. Developer B's directories (`ai_service/`,
`mobile/`, `scripts/smoke_test.sh`) are not touched by this backend.

Shared contracts (`BLUEPRINT.md`, `CONTRACT.md`) are not modified.
