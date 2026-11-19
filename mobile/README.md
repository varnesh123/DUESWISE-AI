# DuesWise — Flutter Mobile Application (Phase 5)

DuesWise is an AI-powered personal finance assistant for India. This is the **Flutter mobile application** (Developer B, Phase 5).

> **Note:** Phase 5 is mock-mode only. It does **not** integrate with the real backend — that is Phase 6. Switching to the live backend requires only replacing `MockFinanceRepository` with `LiveFinanceRepository` behind the same `FinanceRepository` interface.

## Architecture

```
mobile/
├── lib/
│   ├── main.dart                  # Entry point
│   ├── app/
│   │   ├── app.dart               # MaterialApp + GoRouter navigation
│   │   └── router.dart            # Route names
│   ├── config/
│   │   └── app_config.dart        # USE_MOCK_API flag, base URLs
│   ├── core/
│   │   ├── constants/app_constants.dart   # Enums, formats, limits
│   │   ├── errors/app_exception.dart      # Standard error envelope
│   │   ├── utils/money.dart               # Integer-paise Money class
│   │   └── widgets/shared_widgets.dart    # Reusable design-system components
│   ├── data/
│   │   ├── models/             # Typed Dart models (CONTRACTS.md schemas)
│   │   ├── repositories/finance_repository.dart  # Repository interface
│   │   └── mock/
│   │       ├── mock_finance_repository.dart      # Default mock impl
│   │       └── mock_data_loader.dart             # JSON fixture loader
│   └── features/
│       ├── auth/               # Welcome, login, register, persona selection
│       ├── dashboard/          # Balance, safe-to-spend, dues, recent txns
│       ├── transactions/       # List, detail, search, filter, import
│       ├── dues/               # Due list, detail, mark paid
│       ├── subscriptions/      # List, confirm, dismiss
│       ├── insights/           # Nudge list, read/unread
│       ├── scam_detection/     # Message input, mock analysis
│       ├── tax/                # Old vs new regime comparison
│       ├── business/           # Small-business cash flow
│       ├── investments/        # Simulated SIP / portfolio
│       └── settings/           # Profile, notifications, privacy
├── assets/mock_data/           # JSON fixtures (8 files)
└── test/                       # Unit tests
```

## Design system

A single Material 3 design system (`AppTheme`) centralises colours, typography, shapes and component helpers (`CurrencyDisplay`, `CategoryChip`, `RiskBadge`, `EmptyState`, `ErrorState`, `LoadingState`) so every screen shares a consistent fintech identity. Safe-to-spend is visually distinct (green) from total balance (blue).

## Configuration

`USE_MOCK_API` (in `lib/config/app_config.dart`) controls mock vs live:

```dart
static const bool useMockApi = bool.fromEnvironment('USE_MOCK_API', defaultValue: true);
```

Override at build time:

```bash
flutter run --dart-define=USE_MOCK_API=false
```

Mock mode is the default and must remain available throughout the hackathon.

## Money representation

All monetary values are **integer paise** (`Money` class in `lib/core/utils/money.dart`). Conversion to rupees for display happens only in the presentation layer. No floating-point arithmetic is used for financial values.

## Setup

```bash
cd mobile
flutter pub get
flutter run
```

### Android
Requires Flutter SDK + Android SDK / emulator.

### iOS (macOS)
Requires Flutter SDK + Xcode.

```bash
flutter run -d chrome        # web, quickest to verify UI
```

## Running tests

```bash
cd mobile
flutter test
flutter analyze
```

> **Environment note:** The Flutter SDK was not installed on this machine at the time of implementation, so `flutter pub get`, `flutter analyze` and `flutter test` could not be executed here. They must be run once the Flutter SDK is available. No test results are fabricated.

## Screens

| Screen | Purpose |
|---|---|
| Welcome | Entry, demo/persona entry |
| Login / Register | Mock authentication |
| Persona selection | Salaried / young professional / shopkeeper |
| Dashboard | Balance, safe-to-spend, next due, recent transactions |
| Transactions | List, search, category filter, detail, import |
| Dues | Upcoming/paid/overdue, detail, mark paid |
| Subscriptions | Active list, confirm/dismiss detection |
| Insights & nudges | Nudge list, priority, read/unread |
| Scam detection | Sample message input, risk level, safe actions |
| Tax comparison | Old vs new regime, disclaimer |
| Business cash flow | Sales, expenses, receivables, payables, projected balance |
| Investments & SIP | Simulated portfolio (educational, labelled) |
| Settings | Profile, notifications, privacy, demo mode |

## Mock personas (BLUEPRINT §14)

1. **Salaried employee** — ₹60,000/month, EMI, rent, utilities, food, entertainment.
2. **Young professional** — ₹45,000/month, OTT & music subscriptions, recurring payments.
3. **Small shopkeeper** — ₹40,000 opening balance, daily UPI receipts, supplier payables, customer receivables.

All data is synthetic and deterministic.

## Contract compatibility

Typed Dart models mirror `CONTRACTS.md` schemas (snake_case JSON, integer paise, ISO dates, documented enums). The `FinanceRepository` interface is designed so `LiveFinanceRepository` (Phase 6) can be swapped in with no UI changes.

## Mock data

Fixtures live in `assets/mock_data/`: `dashboard.json`, `transactions.json`, `dues.json`, `subscriptions.json`, `nudges.json`, `scam_alerts.json`, `tax_comparison.json`, `business_cashflow.json`, `investments.json`.

## Ownership

Developer B owns `mobile/**`. No files outside `mobile/**` were modified.
