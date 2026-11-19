# DuesWise-AI

## AI-Powered Personal Finance Assistant for India

A personal finance assistant that helps Indian salaried professionals, young professionals, and small business owners understand their finances, anticipate upcoming dues, identify recurring subscriptions, and make more informed spending decisions — entirely with synthetic, privacy-preserving data.

**Warning: This is a hackathon MVP. It does not execute real-money transactions, trading, or require real bank credentials.**

## Problem

Indian salaried individuals and young professionals often struggle to:
- Track recurring subscriptions and dues
- Calculate safe-to-spend amounts after obligations
- Compare old vs new tax regimes
- Detect potentially scam messages
- Manage small-business cash flow

DuesWise-AI solves these problems with deterministic calculations and AI-generated explanations — all with privacy-preserving, synthetic data.

## Architecture

```mermaid
graph TD
    style main fill:#e1f5fe,stroke:#0d47a1,stroke-width:2px
    
    subgraph Frontend
        direction TB
        Mobile[\"Flutter Mobile App\n(Developer B)\"]
    end
    
    subgraph Backend
        direction TB
        AI_Service[\"AI Service\n(Developer A, port 8001)\"]
    end
    
    subgraph Data
        direction TB
        SQLite[\"SQLite Database\n(Managed by Backend)\"]
    end
    
    Frontend --> AI_Service --> SQLite
```

## Key Features

### ✅ Implemented Features

**Mobile Application (Flutter)**
- Dashboard with balance, safe-to-spend, and upcoming dues
- Transaction ingestion and category filtering
- Dues tracking (EMI, rent, insurance, utilities)
- Subscription management (detect, confirm, dismiss)
- Nudge insights and AI-generated insights
- Scam message detection and explanations
- Old vs new tax regime comparison
- Small-business cash-flow overview
- Simulated SIP/investment portfolio (educational)
- Settings with notification preferences
- 3 demo personas (salaried, young professional, shopkeeper)

**AI Service (Flask, port 8001)**
- Merchant normalisation (e.g., "NETFLIX INDIA" → "Netflix")
- Scam explanation (explains risk score from deterministic backend)
- Nudge wording (from backend-supplied financial facts)
- Deterministic fallbacks when no LLM is configured

**Shared Features**
- Demo personas with synthetic data
- Integer paise money representation (₹100 = 10000 paise)
- Mock mode (functional without any backend)
- LLM optional (fallback to deterministic logic)

### Planned / Incomplete Features
- Backend API (Developer A) — not present in this repository
- Live integration between Flutter and backend — configurable but backend not available

---

## Technology Stack

| Technology | Used For |
|---|---|
| Flutter | Mobile application UI, navigation, state management |
| Dart | Mobile app logic, UI widgets |
| FastAPI | AI service (merchant normalisation, scam explanation, nudge wording) |
| Pydantic | Data validation and schemas |
| SQLite | Local database (managed by backend) |
| Python | AI service backend |
| Markdown | Documentation |
| Mermaid | Architecture diagrams |

---

## Project Structure

```
dueswise/
├── BLUEPRINT.md          # Project constitution & business rules
├── CONTRACTS.md          # API contracts between components
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── ai_service/           # Developer A's AI service
│   ├── app/
│ │   ├── main.py          # FastAPI app, /health, error handlers
│ │   ├── config.py        # Environment-driven settings
│ │   ├── api/routes/ai.py # 3 AI endpoints
│ │   ├── schemas/ai.py    # Pydantic v2 request/response models
│ │   ├── services/
│ │   │   ├── merchant_service.py  # Deterministic merchant dict + LLM assist
│ │   │   ├── scam_service.py      # Prompting + output safety validation
│ │   │   ├── nudge_service.py     # Prompting + invented-number guard
│ │   │   └── fallback_service.py  # Deterministic templates
│ │   │   └── services/llm_provider.py # Provider abstraction (HTTP, timeout, retry)
│ │   │   └── utils/
│ │       ├── privacy.py      # Masking, redaction, prompt sanitisation
│ │       └── money.py        # Integer-paise Indian currency formatting
│   ├── tests/              # pytest suite (81 tests, no real LLM calls)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   └── Dockerfile
├── mobile/               # Developer B's Flutter mobile app
│   ├── lib/
│ │   ├── app/             # App setup, router, config
│ │   ├── core/            # Constants, errors, utils, widgets
│ │   ├── data/            # Models, repositories, mock/live data
│ │   ├── features/        # 15 UI screens (dashboard, transactions, etc.)
│ │   └── main.dart        # App entry point
│   ├── data/                # Models, mock data loader, mock repo
│ │   ├── mock/            # MockFinanceRepository + JSON fixtures
│ │   └── models/          # Dart models matching CONTRACTS.md
│   ├── test/                # 37 Flutter tests (mock + live repo)
│   ├── pubspec.yaml         # Dependencies (Flutter, GoRouter, Riverpod, http)
│   └── assets/mock_data/  # 9 JSON fixture files (3 personas × data)
├── BLUEPRINT.md          # Project constitution & business rules
├── CONTRACTS.md          # API contracts (endpoints, schemas, enums)
└── docs/                 # (optional) additional documentation
```

## Getting Started

### Prerequisites

**Flutter Mobile App:**
- Flutter 3.10+ or Flutter 3.16+ (SDK)
- Dart 3.2+ or Dart 3.4+
- Android Studio / Xcode (for emulator/device)
- `flutter` command in PATH
- `dart` command in PATH

**AI Service (Developer A):**
- Python 3.11+ 
- `pip` package manager
- Optional: LLM provider configuration (defaults to deterministic mode)

### Clone the Repository

```bash
git clone https://github.com/varnesh123/DUESWISE-AI.git
cd DUESWISE-AI
```

### Install Dependencies

**AI Service:**
```bash
cd ai_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Mobile App:**
```bash
cd mobile
flutter pub get
```

### Environment Configuration

**AI Service:**
```bash
cd ai_service
cp .envexample .env
# The .env file is pre-configured for deterministic mode:
# AI_PROVIDER=none  (defaults to deterministic fallbacks)
# AI_API_KEY=""        (empty - no LLM calls)
# AI_MODEL=""          (empty - no LLM)
# AI_BASE_URL=""       (empty - uses default)
```

**Mobile App:**
No environment variables required for mock mode. For live mode, configure:
```bash
# In mobile/lib/config/app_config.dart:
# BACKEND_BASE_URL=http://10.0.2.2:8000  (Android emulator)
# or BACKEND_BASE_URL=http://192.168.1.x:8000  (physical device)
```

### Run the AI Service

```bash
cd ai_service
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Successful startup shows:
```
INFO:dueswise.ai:DuesWise AI service ready (env=development, llm_provider=none, llm_enabled=False)
INFO:dueswise.ai:Deterministic fallbacks active; no external LLM will be called
```

Visit: http://localhost:8001/health → {"status":"ok"}

### Run the Mobile Application

**Mock Mode (default, no backend required):**
```bash
cd mobile
flutter pub get
flutter run
```

**Live Mode (with backend):**
```bash
cd mobile
flutter pub get
flutter run --dart-define=USE_MOCK_API=false \
           --dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000
# Android emulator: use 10.0.2.2
# Physical device: use 192.168.1.x (LAN IP)
# iOS simulator: use localhost
```

### Verify Installation

**AI Service:**
```bash
curl -s http://localhost:8001/health
# Expected: {"status":"ok"}
```

**Mobile App:**
- Launch on emulator/device
- Complete persona selection on first launch
- Dashboard should load with synthetic data
- All screens navigable via bottom navigation / sidebar

**Expected Dashboard Values (Salaried Persona):**
- Available Balance: ₹32,000
- Safe to Spend: ₹8,450
- Upcoming Dues Total: ₹2,000
- Safety Reserve: ₹355,000

---

## API Documentation

Summary of key endpoints from `CONTRACTS.md`:

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/auth/login` | POST | No | Authenticate user |
| `/auth/register` | POST | No | Register user |
| `/dashboard/summary` | GET | Yes | Dashboard data |
| `/transactions` | GET | Yes | List transactions |
| `/transactions/ingest` | POST | Yes | Import transaction |
| `/dues` | GET | Yes | List dues |
| `/dues/{id}` | GET | Yes | List dues |
| `/dues/{id}/pay` | POST | Yes | List dues |
| `/subscriptions` | GET | Yes | List subscriptions |
| `/subscriptions/{id}/confirm` | POST | Yes | List subscriptions |
| `/subscriptions/{id}/dismiss` | POST | Yes | List subscriptions |
| `/nudges` | GET | Yes | List nudges |
| `/nudges/{id}/read` | POST | Yes | List nudges |
| `/scam-alerts/analyze` | POST | Yes | Analyze scam message |
| `/scam-alerts` | GET | Yes | List scam alerts |
| `/tax/compare` | POST | Yes | Tax comparison |
| `/business/cashflow` | GET | Yes | Business cash flow |
| `/investments/summary` | GET | Yes | Investment summary |

Full contract at: `CONTRACTS.md`

---

## Testing

**AI Service:**
```bash
cd ai_service
source .venv/bin/activate
python3 -m pytest -q
# 81 tests pass
```

**Mobile App:**
```bash
cd mobile
flutter test --no-pub
# 37 tests pass (22 mock + 15 live)
```

**Flutter Analysis:**
```bash
cd mobile
flutter analyze --no-pub
# 0 errors, 162 info notes (pre-existing)
```

---

## Security and Configuration

- **No real bank credentials** required or used
- **No real money transactions** possible
- **Mock mode** functional without any backend
- **Live mode** requires `BACKEND_BASE_URL` configuration
- **No secrets** committed to repository
- `.env.example` provides safe defaults
- `.gitignore` excludes `.env`, `build/`, generated files

---

## Current Project Status

| Component | Status |
|---|---|
| Mobile Application | ✅ Complete (37/37 tests pass) |
| AI Service | ✅ Complete (81/81 tests pass) |
| Mock Mode | ✅ Fully functional |
| Live Mode | ⚠️ Code path configured, backend not available |
| Backend API | ❌ Not provided in this repository |
| Documentation | ✅ Complete |

**This is a hackathon MVP. It does not execute real-money transactions, trading, or require real bank credentials.**

---

## License

This project is for hackathon evaluation purposes. All code is synthetic and privacy-preserving.

---

## Acknowledgments

- Developed during an AI-for-Finance hackathon
- Flutter mobile framework
- FastAPI for AI service
- Pydantic for data validation
- Mermaid for architecture diagrams

---
*DuesWise-AI — Spend smart, stay ahead*
