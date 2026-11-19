# API integration — as built

This document records how the Flutter client and the FastAPI backend actually talk to
each other, including the mappings implemented during the integration repair and the
places where the implementation intentionally differs from the draft `CONTRACTS.md`.

`CONTRACTS.md` remains the design document. Where the two disagree, this file
describes the running system, and the backend is the executable source of truth.

## 1. Transport conventions

- Base URL: `http://localhost:8000` (configurable in the app via `BACKEND_BASE_URL`).
- All versioned endpoints live under `/api/v1`.
- JSON only; field names are `snake_case`; money is integer paise.
- Authentication: `Authorization: Bearer <demo token>`.
- Errors:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": {}}}
```

Status → code mapping includes `400/422 → VALIDATION_ERROR`, `401 → AUTHENTICATION_REQUIRED`,
`404 → NOT_FOUND`, `405 → METHOD_NOT_ALLOWED`, `409 → DUPLICATE_RESOURCE`,
`413 → PAYLOAD_TOO_LARGE`, `415 → UNSUPPORTED_FILE_TYPE`, `503 → AI_SERVICE_UNAVAILABLE`.

## 2. Operation matrix

| Flutter repository method | Method + path | Notes |
|---|---|---|
| `login` / `register` | `POST /api/v1/auth/demo` | Synthetic session for the selected persona; no passwords |
| `getDashboardSummary` | `GET /api/v1/dashboard/summary` | Direct mapping |
| `getTransactions` | `GET /api/v1/transactions?category=&search=&page_size=` | Envelope key `items`; UI “query” maps to backend `search` |
| `ingestTransaction` | `POST /api/v1/transactions/ingest` | Unified manual/SMS entry point |
| `getDues` | `GET /api/v1/dues` | Envelope key `items` |
| `getDue` | `GET /api/v1/dues/{due_id}` | Added during integration |
| `markDuePaid` | `POST /api/v1/dues/{due_id}/mark-paid` | Body: `{"paid_date": "YYYY-MM-DD"}` |
| `getSubscriptions` | `GET /api/v1/subscriptions` | Envelope key `items` |
| `confirmSubscription` | `POST /api/v1/subscriptions/{id}/confirm` | Direct |
| `dismissSubscription` | `POST /api/v1/subscriptions/{id}/dismiss` | Direct |
| `getNudges` | `GET /api/v1/nudges` | Envelope key `items`; each item has `read` |
| `markNudgeRead` | `POST /api/v1/nudges/{id}/read` | Direct |
| `analyzeScam` | `POST /api/v1/scams/analyze` | Backend returns score/verdict/indicators/explanation/actions |
| `getScamAlerts` | `GET /api/v1/scams` | Envelope key `items`; indicators flattened in the adapter |
| `compareTax` | `POST /api/v1/tax/compare` | Sends `annual_salary_paise` + itemised `deductions` |
| `getBusinessCashflow` | `GET /api/v1/business/cashflow` | Backend field names mapped in the adapter |
| `getInvestmentSummary` | `GET /api/v1/investments/summary` | Portfolio allocation mapped to list items |

Additional backend endpoints not currently used by the app: `POST /api/v1/transactions/manual`,
`POST /api/v1/transactions/ingest/sms`, `POST /api/v1/transactions/ingest/file`,
`POST /api/v1/transactions/ingest/aa-mock`, `POST /api/v1/business/entries`,
`POST /api/v1/business/invoices`, `GET /api/v1/system/status`, `GET /api/v1/auth/me`,
`POST /api/v1/dues`, `PATCH /api/v1/dues/{due_id}`.

## 3. Response envelopes

The backend list endpoints return `{"items": [...], "total": n}` (plus pagination
fields for transactions). The UI models were written against the contract names
(`transactions`, `dues`, `subscriptions`, `nudges`, `scam_alerts`). Rather than
duplicating envelopes, `LiveFinanceRepository._itemsOf()` accepts `items` first and
falls back to the contract key, so both shapes work.

## 4. Authentication

```text
POST /api/v1/auth/demo
{"persona": "salaried" | "young_professional" | "shopkeeper"}

200 OK
{
  "user": {"id": "...", "name": "...", "persona": "salaried", "currency": "INR"},
  "user_id": "...",
  "access_token": "...",          // the demo user's UUID
  "token_type": "bearer",
  "expires_in_minutes": 30
}
```

- The token is opaque to the client and is persisted in `shared_preferences`.
- Every protected query is scoped by the resolved user; cross-user access returns 404.
- `register` intentionally starts the same demo session: there is no account store, so
  creating “accounts” would be fake security. The login screen says so in live mode.
- Production auth remains a roadmap item (see README limitations).

## 5. Unified ingestion

`POST /api/v1/transactions/ingest` accepts either shape:

```jsonc
// manual
{"merchant_raw": "ZOMATO ORDER 8812", "amount_paise": 45500, "transaction_type": "debit",
 "category": "food", "payment_method": "upi", "transaction_date": "2026-11-18"}

// SMS text
{"message": "Rs.499 debited ... for UPI payment to NETFLIX INDIA on 18-11-2026 ..."}
```

Response:

```jsonc
{
  "status": "completed",           // or "duplicate"
  "duplicate": false,
  "warnings": [],
  "transaction": { "...": "TransactionItem" },
  "processing": {"source": "manual", "ai_used": true, "categorisation_confidence": 0.99}
}
```

Behaviour:

- Missing `transaction_date` defaults to today in `Asia/Kolkata`.
- Manual entries are deduplicated by amount, date, type, merchant and payment method.
- Duplicates return the existing transaction with `status: "duplicate"` and a warning.
- Categorisation is deterministic; the AI service is consulted first only when `AI_ENABLED=true`.
- `POST /transactions/manual` and the manual branch of this route call the same service
  (`backend/app/services/manual_transaction.py`), so deduplication and persistence exist
  in one place. The ingest route only adds the ingestion record and categorisation step.

## 6. Field-name adaptations (client adapter)

| Backend field | UI model field |
|---|---|
| `total_sales_paise` | `salesPaise` |
| `total_expenses_paise` | `expensesPaise` |
| `pending_receivables_paise` | `receivablesPaise` |
| `pending_payables_paise` | `payablesPaise` |
| `forecast_date` | `period` |
| `lower_tax_regime` | `recommendedLowerTaxRegime` |
| `estimated_savings_paise` | `estimatedDifferencePaise` |
| `financial_year` | `taxYear` |
| `portfolio[].asset_name` | `InvestmentSummary.label` |
| `portfolio[].value_paise` | `currentValuePaise` |
| `indicators[].description` | `ScamAlert.indicators` / explanation reasons |

## 7. Deliberate deviations from `CONTRACTS.md`

| Contract | As built | Reason |
|---|---|---|
| `POST /auth/login`, `/auth/register` | `POST /auth/demo` | No credential store; honest demo auth instead of fake passwords |
| `POST /transactions/ingest` | Implemented (manual/SMS); plus specialised `/ingest/sms`, `/ingest/file`, `/ingest/aa-mock` | Covers both UI entry and richer ingestion |
| `GET /dues/{id}` | Implemented | Needed by the due-detail screen |
| `POST /dues/{id}/pay` | `POST /dues/{due_id}/mark-paid` | Existing, tested backend route; client updated |
| `/scam-alerts`, `/scam-alerts/analyze` | `/scams`, `/scams/analyze` | Existing route family and schema |
| `annual_income_paise` + `deductions_paise` | `annual_salary_paise` + itemised `deductions` | Backend computes regime-specific deductions |
| Nudge `read` | Backend now returns both `status` and `read` | UI consumes `read`; status retained |

## 8. AI service contract (backend → AI)

| Call | Used by backend? | Purpose |
|---|---|---|
| `POST /api/v1/ai/merchant-normalize` | **Yes** (when `AI_ENABLED=true`) | Normalise unknown merchants during ingestion |
| `POST /api/v1/ai/explain-scam` | No (endpoint implemented and tested) | Future richer explanations |
| `POST /api/v1/ai/generate-nudge` | No (endpoint implemented and tested) | Future nudge wording |

The backend `AIClient` enforces a 5 second timeout, at most one retry, schema validation,
and returns `None` on any failure so ingestion continues deterministically.

Verified end-to-end: with `AI_ENABLED=true` and the AI service running, ingestion returns
`processing.ai_used == true`, and the AI service log shows the `merchant-normalize` call.

## 9. Running the integration suite

```bash
cd mobile
flutter test test/integration/live_backend_test.dart \
  --dart-define=LIVE_BACKEND=http://127.0.0.1:8099 \
  --dart-define=EXPECT_AI=true
```

The suite performs real HTTP against a real backend and database (no mocks) and covers:
demo login, dashboard, manual ingestion, filtering/search, due create → detail → mark paid,
subscriptions, nudges, scam analysis + alert listing, tax comparison, cash flow,
investments, and unauthenticated error handling.

## 10. Compatibility checklist for future changes

1. Add or change a backend route → update this file and the adapter in
   `mobile/lib/data/live/live_finance_repository.dart`.
2. Keep list envelopes consistent (`items`) or extend `_itemsOf`.
3. Never introduce floating-point money.
4. Keep AI calls optional and non-fatal.
5. Add a backend test and, for client-visible changes, a test in
   `mobile/test/live_adapters_test.dart` or the live suite.
