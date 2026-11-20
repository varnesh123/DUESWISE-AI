# DuesWise-AI — `frontend-integration` snapshot

> **Historical branch.** This branch records an early integration snapshot and is
> **superseded by [`main`](https://github.com/varnesh123/DUESWISE-AI/tree/main)**.
> Use `main` (or the default `varnesh/phase-6-integration` branch) for the current,
> runnable project and its documentation.

## What this branch contains

At commit `8bdbe26` this branch combined the initial Flutter project structure with
the backend foundation:

```text
frontend-integration/
├── backend/       # FastAPI + SQLite backend foundation
├── ai_service/    # Advisory FastAPI microservice
├── mobile/        # Flutter source, assets and offline tests
├── BLUEPRINT.md   # Product blueprint
└── CONTRACTS.md   # API contract
```

Component guides live in [`backend/README.md`](backend/README.md),
[`ai_service/README.md`](ai_service/README.md), and
[`mobile/README.md`](mobile/README.md).

## What this branch does not contain

Compared with `main`, this snapshot predates:

- the `docs/` directory (architecture, setup, API integration),
- Flutter Android, iOS, and web platform runners,
- the live backend HTTP integration test suite,
- the AI service `.env.example` template,
- the verified root README, screenshots, and release documentation.

## Current project

For installation, architecture, API documentation, testing, and limitations, see the
root [`README.md`](https://github.com/varnesh123/DUESWISE-AI/blob/main/README.md) on
`main`.
