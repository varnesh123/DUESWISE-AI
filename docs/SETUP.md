# Setup guide

This guide takes you from a fresh clone to a running app. Follow it in order.

## 0. What you need

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| pip | any recent | `python3 -m pip --version` |
| Flutter SDK | 3.35+ (Dart 3.9+) | `flutter --version` |
| Git | any | `git --version` |

Optional: Android Studio or Xcode if you want to run on a device/emulator. Desktop or Chrome targets work too.

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

### Create a demo session

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

1. Welcome → **Continue** → persona selection.
2. Log in (live mode shows a demo-mode note; any email/password works because it starts a synthetic persona session).
3. Dashboard loads balance/safe-to-spend.
4. Transactions → **+ Import** → enter a merchant and amount → the row appears and filters find it.
5. Dues → open a due → **Mark as paid**.
6. Subscriptions → confirm or dismiss.
7. Insights → mark a nudge read.
8. Scam detection → paste a sample → analyze.
9. Tax → compare regimes.
10. Business / Investments load.

## 5. Run the tests

```bash
# Backend
cd backend && pytest -q

# AI service
cd ai_service && pytest -q

# Flutter
cd mobile && dart analyze && flutter test
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

Expected: 9 tests passing. `EXPECT_AI=true` asserts that the backend actually called the AI service during ingestion. Without `LIVE_BACKEND`, that suite is skipped.

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
| 401 `AUTHENTICATION_REQUIRED` | You need `Authorization: Bearer <demo token>`; create a session first. |
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
