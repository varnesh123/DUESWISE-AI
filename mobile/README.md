# DuesWise Flutter App

The mobile client for DuesWise — a personal finance assistant for India.
It runs fully offline in **mock mode** and can switch to the live backend.

## Requirements

| Tool | Version |
|---|---|
| Flutter | **3.35+** (Dart 3.9+) — verified with Flutter 3.35.7 / Dart 3.9.2 |
| Backend (live mode) | see `../backend/README.md` |

> Older SDKs fail dependency resolution: `flutter_localizations` pins `intl 0.20.2`,
> which older Dart SDKs cannot satisfy.

## Install and run

```bash
cd mobile
flutter pub get
flutter run              # Android/iOS device or emulator
flutter run -d chrome    # quickest way to try the UI
```

Mock mode is the default (`USE_MOCK_API=true`); no servers are required.

Platform runners for Android, iOS and web are generated in `android/`, `ios/` and
`web/`. `flutter build web --release` is verified in this repository.

### Live mode

```bash
flutter run \
  --dart-define=USE_MOCK_API=false \
  --dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000   # Android emulator
```

| Target | Base URL |
|---|---|
| Android emulator | `http://10.0.2.2:8000` |
| iOS simulator / desktop | `http://localhost:8000` |
| Physical device | `http://<LAN-IP>:8000` |

In live mode the login/register screens start a **synthetic demo session**
(`POST /api/v1/auth/demo`) for the selected persona. Any email/password is accepted
because no real account exists — the app states this on screen.

## Architecture

```text
lib/
├── main.dart                     # entry point
├── app/
│   ├── app.dart                  # MaterialApp.router + GoRouter routes
│   ├── router.dart               # path constants
│   └── repository_provider.dart  # mock/live repository selection
├── config/app_config.dart        # USE_MOCK_API, backend base URL
├── core/
│   ├── constants/                # categories, limits, formats
│   ├── errors/app_exception.dart # contract-shaped exceptions
│   ├── utils/money.dart          # integer-paise Money
│   └── widgets/                  # theme + shared components
├── data/
│   ├── models/                   # typed models
│   ├── repositories/             # FinanceRepository interface
│   ├── live/                     # ApiClient + LiveFinanceRepository
│   └── mock/                     # MockFinanceRepository + fixture loader
└── features/                     # one folder per screen area
```

Screens depend only on `FinanceRepository`. `LiveFinanceRepository` is the adapter
between backend JSON and the UI models (envelopes, field names, demo auth, scam
indicators). See `../docs/API_INTEGRATION.md`.

### Money

All values are integer paise; `Money` handles formatting only.
No floating-point arithmetic is used for financial values.

## Screens

| Screen | Purpose |
|---|---|
| Welcome | Entry point; persona, login, register |
| Login / Register | Demo session (live) or simulated auth (mock) |
| Persona selection | Salaried / young professional / shopkeeper |
| Dashboard | Balance, safe-to-spend, next due, recent transactions |
| Transactions | List, search, category filter, detail, import |
| Dues | Upcoming/paid/overdue, detail, mark paid |
| Subscriptions | Confirm/dismiss detections |
| Insights | Nudges with read/dismiss |
| Scam detection | Analyse a pasted message |
| Tax comparison | Old vs new regime with disclaimer |
| Business cash flow | Sales, expenses, receivables, payables, projection |
| Investments | Simulated educational portfolio |
| Settings | Persona, notifications, nudge cap, demo notice |

Every data screen has loading, empty, error-with-retry and success states.

## Tests

```bash
cd mobile
dart analyze          # 0 errors
flutter test          # 45 tests
```

Coverage includes:

- money formatting and integer arithmetic,
- JSON parsing for every model,
- mock repository behaviour,
- API client paths/headers/errors,
- live repository adapters (query params, `items` envelopes, demo auth, tax,
  cash-flow, investments, scam indicators).

### Live end-to-end tests (real HTTP, no mocks)

Requires a running backend (and AI service if `EXPECT_AI=true`):

```bash
flutter test test/integration/live_backend_test.dart \
  --dart-define=LIVE_BACKEND=http://127.0.0.1:8099 \
  --dart-define=EXPECT_AI=true
```

9 tests cover login, dashboard, ingestion, filtering, dues lifecycle, subscriptions,
nudges, scam analysis, tax, cash flow, investments and unauthenticated errors.
The suite skips itself when `LIVE_BACKEND` is not set, so `flutter test` stays green
offline.

## Mock data

`assets/mock_data/` contains deterministic fixtures for dashboard (per persona),
transactions, dues, subscriptions, nudges, scam alerts, tax, cash flow and investments.
All data is synthetic.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `version solving failed` (`intl`) | Upgrade Flutter to 3.35+. |
| Blank/loading dashboard in live mode | Backend unreachable or wrong `BACKEND_BASE_URL`; the screen should show a retry. |
| `UNAUTHORIZED` | Log in again — the demo token was cleared or invalid. |
| Android emulator cannot connect | Use `10.0.2.2`. |
| Stale generated files | `flutter clean && flutter pub get`. |

## Limitations

- No production authentication; demo sessions only.
- No offline cache of live data — mock mode is the offline story.
- Investments are simulated; no market data.
- UI is verified by tests and manual runs; no CI/device farm yet.
