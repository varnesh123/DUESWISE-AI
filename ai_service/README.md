# DuesWise AI Service

Independent, advisory FastAPI microservice for DuesWise AI. It provides three
capabilities:

1. **Merchant normalisation** — turn noisy payment strings into clean merchant
   names with a suggested category.
2. **Scam explanation** — explain a risk assessment that the deterministic
   backend has already produced.
3. **Nudge wording** — phrase a nudge from financial facts the backend supplies.

The service never calculates safe-to-spend, taxes, SIP values, risk scores or any
other authoritative financial result. It does not import backend code and has no
database access.

## Backend integration

The backend's `AIClient` calls `POST /api/v1/ai/merchant-normalize` during
transaction ingestion when `AI_ENABLED=true`. This path is verified end-to-end by
`mobile/test/integration/live_backend_test.dart` (run with `--dart-define=EXPECT_AI=true`),
which asserts that the ingest response reports `processing.ai_used == true` against a
running service. Failures, timeouts and invalid responses fall back silently to the
backend's deterministic categoriser.

The scam-explanation and nudge endpoints are implemented and unit-tested, but the
backend currently generates its own deterministic text for those flows; wiring them
in is a roadmap item.

## Architecture

```text
Flutter  ──HTTP──▶  Backend (Developer A, :8000)  ──HTTP──▶  AI service (:8001)  ──▶  LLM (optional)
```

- Endpoints follow `CONTRACTS.md` and `BLUEPRINT.md`.
- Every endpoint works with `AI_PROVIDER=none` using deterministic local logic.
- The LLM is used selectively: known merchants and complete nudge facts are
  handled locally; otherwise, if a provider is configured, the LLM may improve
  wording. Any failure, timeout, invalid output or unsafe output reverts to the
  deterministic path.
- Provider responses are validated with Pydantic before use.

### Folder structure

```text
ai_service/
├── app/
│   ├── main.py                 # FastAPI app, /health, error handlers, CORS
│   ├── config.py               # Environment-driven settings
│   ├── api/routes/ai.py        # Three AI endpoints
│   ├── schemas/ai.py           # Pydantic request/response models
│   ├── services/
│   │   ├── merchant_service.py # Deterministic merchant dictionary + LLM assist
│   │   ├── scam_service.py     # Prompting + output safety validation
│   │   ├── nudge_service.py    # Prompting + invented-number guard
│   │   ├── llm_provider.py     # Provider abstraction (HTTP, timeout, retry)
│   │   └── fallback_service.py # Deterministic templates
│   └── utils/
│       ├── privacy.py          # Masking, redaction, prompt sanitisation
│       └── money.py            # Integer-paise Indian currency formatting
├── tests/                      # pytest suite (no real LLM calls)
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Setup

```bash
cd ai_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # optional; defaults already work
```

The service needs Python 3.11+.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `none` | `none`, `openai_compatible`, `openai`, or `groq` |
| `AI_API_KEY` | empty | Provider key; never commit it |
| `AI_MODEL` | empty | Model identifier |
| `AI_BASE_URL` | provider default | Any OpenAI-compatible `/v1` base URL |
| `AI_TIMEOUT_SECONDS` | `5` | Per-attempt HTTP timeout |
| `AI_MAX_RETRIES` | `1` | Retry count, capped at 1 |
| `HOST` / `PORT` | `0.0.0.0` / `8001` | Bind address |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ALLOW_ORIGINS` | empty | Comma-separated; middleware disabled when empty |

The `LLM_*` names from the phase prompt (`LLM_API_KEY`, `LLM_MODEL`,
`LLM_BASE_URL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`) are accepted as
aliases. If a provider is requested without a key, model or base URL, the
service logs a warning and runs deterministically.

## Run

```bash
cd ai_service
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Or from the repository root:

```bash
cd ai_service && python3 -m uvicorn app.main:app --port 8001
```

Interactive docs: <http://localhost:8001/docs>

### Docker

```bash
docker build -t dueswise-ai-service ai_service
docker run --rm -p 8001:8001 --env-file ai_service/.env.example dueswise-ai-service
```

## Tests

```bash
cd ai_service
python3 -m pytest -q
```

No network access or paid key is required: tests override the provider
dependency with a fake and use `httpx.MockTransport` for provider behaviour.

## Endpoint examples

### Health

```bash
curl -s http://localhost:8001/health
# {"status":"ok"}
```

### Merchant normalisation

```bash
curl -s -X POST http://localhost:8001/api/v1/ai/merchant-normalize \
  -H 'Content-Type: application/json' \
  -d '{"merchant_raw":"NETFLIX INDIA PVT LTD","currency":"INR"}'
# {"merchant_normalized":"Netflix","canonical_name":"Netflix",
#  "category":"entertainment","confidence":0.93,"fallback_used":false}
```

Unknown merchants return a cleaned name with `category: "other"`, low confidence
and `fallback_used: true` (or are improved by the LLM when configured).

### Scam explanation

```bash
curl -s -X POST http://localhost:8001/api/v1/ai/explain-scam \
  -H 'Content-Type: application/json' \
  -d '{"risk_score":96,"risk_level":"critical",
       "indicators":["Suspicious external link","Requests UPI PIN"],
       "message":"Your account will be blocked. Share your UPI PIN."}'
# {"summary":"This message shows strong signs of a phishing attempt ...",
#  "reasons":["Suspicious external link","Requests UPI PIN"],
#  "safe_action":"Do not open any links ... Do not share your OTP, UPI PIN ..."}
```

The service never returns or recalculates a risk score. The response is
deliberately cautious and never states that a message is definitely fraudulent.

### Nudge generation

```bash
curl -s -X POST http://localhost:8001/api/v1/ai/generate-nudge \
  -H 'Content-Type: application/json' \
  -d '{"category":"entertainment","spending_increase_percent":35,
       "upcoming_due":"Home EMI","amount_paise":1200000,"days_until_due":5}'
# {"title":"Upcoming payment reminder",
#  "message":"Your Home EMI is due in 5 days. Setting aside about ₹12,000 ...",
#  "fallback_used":true}
```

The backend decides eligibility; this endpoint only words the message. All
fields are optional, but the service never invents facts that were not supplied.

### Error format

```json
{"error": {"code": "VALIDATION_ERROR", "message": "Invalid request payload.", "details": {"errors": []}}}
```

## Contract notes

The two authoritative documents disagree in one place:

- `CONTRACTS.md` §5.1 names the merchant field `merchant_normalized`.
- `BLUEPRINT.md` §9 names it `canonical_name` and adds `fallback_used`.

To keep both consumers working without editing shared documents, the merchant
response returns all three fields (`merchant_normalized`, `canonical_name`,
`fallback_used`). Scam and nudge response shapes follow `BLUEPRINT.md` §9, which
is the only place those schemas are defined. The scam request accepts the
BLUEPRINT fields plus an optional `message` (max 2000 characters), which is
masked and truncated before any prompt.

## Privacy and security design

- **Masking before prompts:** account/Aadhaar-style numbers (9–18 digits), UPI
  IDs and Indian mobile numbers are masked; OTP/PIN/password/CVV values are
  replaced with `[REDACTED]`.
- **No full statements:** merchant strings are capped at 200 characters and only
  a 600-character masked message excerpt can reach a provider.
- **Selective LLM use:** common merchants are resolved locally; prompts contain
  only the facts needed for wording.
- **Untrusted input:** system prompts state that message/merchant text is
  untrusted data, never instructions.
- **No definitive fraud claims:** outputs containing certainty language are
  rejected and replaced with the deterministic explanation.
- **No invented money:** nudge output is rejected if it contains a number that
  was not supplied by the backend, or phrases such as "safe to spend" or
  "you can afford".
- **Credential warnings always present:** scam `safe_action` always warns against
  sharing OTP/PIN/password.
- **No sensitive logging:** request bodies, prompts and provider responses are
  never logged. Validation errors do not echo offending input.
- **No stack traces or secrets in responses:** generic `INTERNAL_ERROR` only.
- **Conservative CORS:** disabled by default.
- **No persistence:** the service is stateless and stores no user financial data.
- **Secrets only in environment variables:** no keys are hardcoded or committed.

## Known limitations

- Merchant coverage is a curated dictionary, not an exhaustive merchant
  database; unknown names fall back with low confidence.
- The LLM path is OpenAI-compatible chat-completions only; no vendor SDKs.
- The service does not authenticate callers. If the backend and AI service are
  exposed beyond localhost, add network-level access control (for example an
  internal service token) by joint agreement, since it affects the contract.
- The scam request `message` field is an additive extension used for better
  explanations; omit it and the service still works.
