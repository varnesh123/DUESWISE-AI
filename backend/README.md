# DuesWise Backend

FastAPI service that owns DuesWise's financial logic, persistence, demo sessions
and API contract. Port **8000**.

- No real banking data, credentials or transactions.
- All amounts are integer paise.
- Every protected query is scoped to the authenticated user.

## Tech stack

- Python 3.11+
- FastAPI + Pydantic v2
- SQLAlchemy 2.x + SQLite
- uvicorn
- pytest + httpx (tests)
- python-multipart (uploads), pdfplumber (PDF statements)

## Install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # optional; defaults work
```

## Run

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- Health: <http://localhost:8000/health>
- OpenAPI UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

The SQLite file (`dueswise.db`) is created on startup. To create tables manually:

```bash
python -c "from app.database import init_db; init_db()"
```

## Configuration

Environment variables are read from the environment and from `backend/.env`.
See [`.env.example`](.env.example) for the full list. The important ones:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dueswise.db` | Database location |
| `AI_ENABLED` | `false` | Enable calls to the AI service |
| `AI_SERVICE_BASE_URL` | `http://localhost:8001` | AI service origin |
| `FORECAST_HORIZON_DAYS` | `30` | Safe-to-spend horizon |
| `SAFETY_RESERVE_PERCENT` | `10` | Reserve percentage |
| `MAX_FILE_SIZE_MB` | `10` | Statement upload limit |

## Authentication

The MVP uses **synthetic demo sessions**, not production auth:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/demo \
  -H 'Content-Type: application/json' -d '{"persona":"salaried"}'
```

Response includes `user`, `user_id`, `access_token` (= demo user UUID),
`token_type`, `expires_in_minutes`. Send it as:

```http
Authorization: Bearer 11111111-1111-4111-8111-111111111111
```

Personas: `salaried`, `young_professional`, `shopkeeper`.
There are no passwords, registration or token-expiry enforcement — do not treat this
as real security. Production auth is a roadmap item.

## Endpoints

### Health and system

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Process health (unversioned) |
| GET | `/api/v1/system/status` | App name/version/env + database status |

### Auth

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/auth/demo` | Create demo session |
| GET | `/api/v1/auth/me` | Current user (bearer) |

### Dashboard

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | Safe-to-spend with disclosed components |

### Transactions

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/transactions` | Paginated; filters: `category`, `transaction_type`, `from_date`, `to_date`, `search` |
| GET | `/api/v1/transactions/{transaction_id}` | Single transaction |
| POST | `/api/v1/transactions/manual` | Manual creation |
| POST | `/api/v1/transactions/ingest` | Unified entry: manual fields or `message` (SMS) |

### Ingestion

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/transactions/ingest/sms` | Parse one SMS |
| POST | `/api/v1/transactions/ingest/file` | Multipart CSV/PDF upload |
| POST | `/api/v1/transactions/ingest/aa-mock` | Synthetic Account Aggregator payload |

### Dues

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/dues` | Filters: `status`, `from_date`, `to_date` |
| POST | `/api/v1/dues` | Create |
| GET | `/api/v1/dues/{due_id}` | Detail |
| PATCH | `/api/v1/dues/{due_id}` | Partial update |
| POST | `/api/v1/dues/{due_id}/mark-paid` | Body `{"paid_date":"YYYY-MM-DD"}` |

### Subscriptions

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/subscriptions` | List |
| POST | `/api/v1/subscriptions/{id}/confirm` | Confirm detection |
| POST | `/api/v1/subscriptions/{id}/dismiss` | Dismiss detection |

### Nudges

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/nudges` | Includes `status` and `read` |
| POST | `/api/v1/nudges/{id}/read` | Mark read |
| POST | `/api/v1/nudges/{id}/dismiss` | Dismiss |

### Scam detection

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/scams/analyze` | Deterministic score + indicators + explanation |
| GET | `/api/v1/scams` | Stored alerts |

### Tax, business, investments

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/tax/compare` | Old vs new regime; rule-backed financial years only |
| GET | `/api/v1/business/cashflow` | Projected cash balance |
| POST | `/api/v1/business/entries` | Sale/expense/receivable/payable |
| POST | `/api/v1/business/invoices` | Illustrative GST invoice |
| GET | `/api/v1/investments/summary` | Simulated educational summary |

List endpoints return `{"items": [...], "total": n}`; transactions also return
`page` and `page_size`.

## AI service integration

`app/services/ai_client.py` calls the AI service only for merchant normalisation and
only when `AI_ENABLED=true`. It enforces a timeout, at most one retry, validates the
response schema, and returns `None` on any failure so ingestion never breaks.
Scam explanations and nudge wording remain deterministic in the backend.

## Tests

```bash
cd backend
pytest -q                  # 175 tests
```

- Unit tests cover money, dates, parsers, forecasters, tax, scam rules, categorisation,
  error handling and repositories.
- Integration tests exercise every router through `TestClient` with an isolated
  temporary SQLite database.

## Project layout

```text
backend/
├── app/
│   ├── api/routes/     # thin routers
│   ├── models/         # SQLAlchemy tables
│   ├── repositories/   # user-scoped queries
│   ├── schemas/        # Pydantic contracts
│   ├── services/       # financial + parsing logic, AI client
│   ├── rules/          # categories, merchant aliases, tax rules (JSON)
│   ├── utils/          # money, dates, logging, masking
│   ├── config.py       # settings
│   ├── database.py     # engine/session/init
│   ├── dependencies.py # DB session + current user
│   └── main.py         # app + error handlers
├── tests/              # unit/ and integration/
├── requirements.txt
└── Dockerfile
```

## Limitations

- Demo auth only; no real account system.
- No migrations (schema created via `create_all`).
- SQLite is not suitable for concurrent production use.
- Tax rules currently cover a single financial year and are marked unverified.
- PDF ingestion supports text-based PDFs only.
