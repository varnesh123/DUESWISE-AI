# Setup guide

This guide takes you from a fresh clone to a running app. Follow it in order.

## 0. What you need

| Tool | Minimum | Verified version in this release | Check |
|---|---|---|---|
| Python | 3.11+ | 3.14.5 | `python3 --version` |
| pip | any recent | 26.1.1 | `python3 -m pip --version` |
| Flutter SDK | 3.35+ | 3.50.0 (stable) | `flutter --version` |
| Dart | 3.9+ | 3.14.0 | `dart --version` |
| SQLite | bundled with Python | 3.50.4 | `python3 -c "import sqlite3; print(sqlite3.sqlite_version)"` |
| Git | any | any | `git --version` |

Optional: Android Studio (Java 17 + Android SDK) or Xcode if you want to run on a device/emulator. Desktop or Chrome targets work too and need no extra SDK.

> **Verified in this release:** backend tests (`185 passed`), AI tests (`81 passed`),
> Flutter tests (`54 passed`), live E2E (`12 passed`), and
> `flutter build web --release`. **Android was not verified** because no Java runtime or
> Android SDK is installed on the verification machine.

> **Do not use Flutter 3.24 or older.** `flutter_localizations` pins `intl 0.20.2`, and older Dart SDKs cannot resolve it.

## 1. Clone and install Python dependencies

```bash
git clone https://github.com/varnesh123/DUESWISE-AI.git
cd DUESWISE-AI

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r backend/requirements.txt
pip install -r ai_service/requirements-dev.txt
```

You can use one virtual environment for both Python services, or create one per component (`backend/.venv`, `ai_service/.venv`).

## 2. Start the backend

```bash
cd backend
cp .env.example .env               # optional, defaults work
uvicorn app.main:app --reload --port 8000
```

Verify in another terminal:

```bash
curl -s http://localhost:8000/health
# {"status":"ok"}

curl -s http://localhost:8000/openapi.json | head -c 80
```

First start creates `backend/dueswise.db`.

### Create a real account (recommended)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"at-least-8-chars","name":"Your Name"}'
```

The response contains `access_token` (an opaque session token, valid for 7 days) and
`user`. Use it as a bearer token:

```bash
TOKEN=<access_token from the response>
curl -s http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```

Sign in again at any time with `POST /api/v1/auth/login` using the same email/password.
`POST /api/v1/auth/logout` revokes the current session. Passwords are stored only as
PBKDF2-HMAC-SHA256 hashes; session tokens are stored only as SHA-256 digests.

### Create a synthetic demo session (optional)

Demo mode is deliberately separate from real accounts and never auto-logs-in.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/demo \
  -H 'Content-Type: application/json' \
  -d '{"persona":"salaried"}'
```

Copy the `access_token` from the response and use it as a bearer token:

```bash
TOKEN=11111111-1111-4111-8111-111111111111   # salaried demo user
curl -s http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```

Personas: `salaried`, `young_professional`, `shopkeeper`.

## 3. Start the AI service (optional)

```bash
cd ai_service
cp .env.example .env               # defaults: deterministic, no LLM key
uvicorn app.main:app --reload --port 8001
```

```bash
curl -s http://localhost:8001/health
# {"status":"ok"}

curl -s -X POST http://localhost:8001/api/v1/ai/merchant-normalize \
  -H 'Content-Type: application/json' \
  -d '{"merchant_raw":"NETFLIX INDIA PVT LTD","currency":"INR"}'
```

To let the backend use it, in `backend/.env`:

```env
AI_ENABLED=true
AI_SERVICE_BASE_URL=http://localhost:8001
```

Restart the backend. Ingested merchants will now be normalised by the AI service when it is reachable; otherwise the deterministic fallback is used.

## 4. Run the Flutter app

### Mock mode (fastest, no servers)

```bash
cd mobile
flutter pub get
flutter run              # device/emulator
flutter run -d chrome    # browser (no device needed)
```

Android, iOS and web runners are present in the repository.

### Live mode

Android emulator:

```bash
flutter run \
  --dart-define=USE_MOCK_API=false \
  --dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000
```

Desktop / iOS simulator:

```bash
flutter run \
  --dart-define=USE_MOCK_API=false \
  --dart-define=BACKEND_BASE_URL=http://localhost:8000
```

Physical device: use `http://<your-computer-LAN-IP>:8000` and make sure the phone is on the same network.

### What to check in the app

1. Welcome → **Create account** (or **Log in**) for a real, private account.
   **Continue with demo data** is a separate button that starts a synthetic persona.
2. After registering, the dashboard loads with a greeting and empty states.
3. Transactions → **Add** → enter merchant, amount, type, category, date → save.
   Edit or delete from the transaction detail screen; search and sort with the toolbar.
4. Dues → **Add** → enter a title, amount, due date, type, frequency → save.
   Open it to edit, delete, or mark it paid. Filter by status and sort.
5. Subscriptions → confirm or dismiss.
6. Insights → mark a nudge read.
7. Scam detection → paste a sample → analyze.
8. Tax → compare regimes.
9. Business / Investments load.
10. Settings → shows your account email and **Log out** revokes the session.

Mock mode (`USE_MOCK_API=true`, the default) keeps everything in memory and never sends
network requests. Live mode (`--dart-define=USE_MOCK_API=false`) uses the real backend,
real accounts, and persistent records.

### Android setup (only if you target Android)

No Android SDK is required for web/desktop. To build an APK:

1. Install Java 17 (for example Temurin) and Android Studio.
2. In Android Studio, install the Android SDK and an emulator image.
3. Accept licences: `flutter doctor --android-licenses`.
4. Confirm with `flutter doctor` and `flutter devices`.
5. Point the app at your machine with `--dart-define=BACKEND_BASE_URL=http://10.0.2.2:8000`
   (the emulator's alias for your host).

## 5. Run the tests

```bash
# Backend (185 tests)
cd backend && pytest -q

# AI service (81 tests)
cd ai_service && pytest -q

# Flutter (54 tests; live HTTP suite skips without LIVE_BACKEND)
cd mobile && flutter analyze && flutter test
```

### Live end-to-end test (real HTTP)

Start the backend on port 8099 with an isolated database and enable the AI service:

```bash
# terminal 1
cd ai_service && uvicorn app.main:app --port 8001

# terminal 2
cd backend
DATABASE_URL=sqlite:////tmp/dueswise_e2e.db \
AI_ENABLED=true \
AI_SERVICE_BASE_URL=http://127.0.0.1:8001 \
uvicorn app.main:app --port 8099

# terminal 3
cd mobile
flutter test test/integration/live_backend_test.dart \
  --dart-define=LIVE_BACKEND=http://127.0.0.1:8099 \
  --dart-define=EXPECT_AI=true
```

Expected: 12 tests passing. `EXPECT_AI=true` asserts that the backend actually called the AI service during ingestion. Without `LIVE_BACKEND`, that suite is skipped.

## 6. Ports at a glance

| Service | Port | URL |
|---|---|---|
| Backend | 8000 | http://localhost:8000/docs |
| AI service | 8001 | http://localhost:8001/docs |
| Live E2E backend | 8099 | http://127.0.0.1:8099 |

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| `version solving failed` for `intl` | Upgrade Flutter to 3.35+ (Dart 3.9+). |
| `ModuleNotFoundError: app` | Run `uvicorn`/`pytest` from inside `backend/` or `ai_service/`. |
| `Address already in use` | Stop the other process or pass `--port 8010`. |
| 401 `AUTHENTICATION_REQUIRED` | Sign in again. You need `Authorization: Bearer <session token>`; register/login or create an explicit demo session first. |
| 409 `DUPLICATE_RESOURCE` on register | That email already has an account; use **Log in** instead. |
| Secure storage error on desktop/web tests | Tests fall back to `shared_preferences`; no action needed. On a real device, ensure Keychain/Keystore is available. |
| Android emulator cannot connect | Use `10.0.2.2`, not `localhost`. |
| AI features not used | Set `AI_ENABLED=true` and confirm `/health` on port 8001. |
| App stuck on a loading screen | The backend is unreachable; the screen should show a retryable error. Check the base URL. |
| `pubspec.lock` missing after clone | Run `flutter pub get`. |

## 8. Reset local state

```bash
# Backend database
rm -f backend/dueswise.db

# Flutter build artefacts and packages
cd mobile && flutter clean && flutter pub get
```
