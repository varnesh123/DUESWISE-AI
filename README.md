# DuesWise AI

### Your Intelligent AI-Powered Payment Management Assistant

DuesWise AI is an intelligent financial payment management platform designed to help users stay ahead of their bills, subscriptions, recurring payments, and financial obligations.

Instead of manually remembering payment dates and checking multiple platforms, DuesWise brings payment information together in one place and aims to provide a personalized AI assistant that helps users understand, manage, and prepare for upcoming payments.

The long-term vision is to build an AI agent that proactively monitors payment obligations, tracks available balances where supported, sends personalized reminders, warns users about potential insufficient balances, and eventually assists with payment actions with explicit user approval.

---

## 1. Project Vision

Managing multiple financial commitments can become difficult:

- Bills have different due dates.
- Subscriptions renew automatically.
- Payments are spread across different platforms.
- Users may forget upcoming payment deadlines.
- Available balances may be insufficient when payments are due.
- Tracking recurring expenses manually takes time.

**DuesWise AI aims to solve these problems through one intelligent payment assistant.**

The central objective is not simply to display financial information. It is to help users stay informed, prepared, and in control of their payments through personalized and proactive assistance.

## 2. Core Features

### 2.1 Financial Account Management
- Manage financial accounts and connected institutions.
- View available account balances where supported.
- Support a provider-based financial data integration architecture.
- Track connection and synchronization status.
- Clearly distinguish mock data from real connected financial data.

### 2.2 Transaction Management
- Retrieve and store financial transactions.
- Categorize income and expenses.
- View transaction history.
- Filter transactions by date, category, account, and other supported criteria.
- Add and manage manual transactions.
- Prevent accidental duplicate transactions.
- Support transaction ingestion through supported sources.

### 2.3 Bill Management
- Create, edit, and manage bills.
- Track payment due dates.
- Identify upcoming, due, overdue, and completed bills.
- Support recurring and one-time bills.
- Maintain payment history.

### 2.4 Subscription Management
- Track recurring subscriptions.
- Manage subscription details and renewal dates.
- View subscription payment history.
- Pause, resume, or manage subscriptions where supported.
- Identify potential recurring payment patterns.

### 2.5 Unified Financial Dashboard
- View an overview of financial accounts.
- Monitor income and expenses.
- View upcoming payments.
- Track bills and subscriptions.
- Review recent transactions.
- Monitor account synchronization status.
- Access payment information through web and mobile interfaces.

### 2.6 Intelligent AI Payment Assistant — Core Product Direction

The AI assistant is the central part of DuesWise.

Its intended capabilities include:

- Track upcoming bills, subscriptions, and recurring dues.
- Understand individual payment patterns.
- Generate personalized payment reminders.
- Notify users before payment deadlines.
- Monitor available balances where supported.
- Warn users when their available balance may be insufficient for upcoming payments.
- Prioritize payment obligations based on due dates and available funds.
- Answer questions about payment history and upcoming obligations.
- Proactively assist users in managing their payment schedules.
- Eventually assist with payment actions, only after explicit user approval.

The assistant should provide useful, context-aware notifications rather than generic reminders.

**Important:** AI-driven autonomous reasoning and payment assistance are future development capabilities. Their implementation status must be tracked in the project blueprint rather than assumed to be complete.

---

## 3. Application Architecture

DuesWise follows a modular architecture with separate backend, web, and mobile applications.

```text
                 DUESWISE AI
                      |
          +-----------+-----------+
          |                       |
      Web App                Mobile App
          |                       |
          +-----------+-----------+
                      |
                  REST API
                      |
                FastAPI Backend
                      |
        +-------------+-------------+
        |             |             |
     Accounts     Transactions   Payments
        |             |             |
        +-------------+-------------+
                      |
                Service Layer
                      |
               Repository Layer
                      |
                  Database
                      |
          Financial Data Providers
                      |
             AI Assistant Layer
             (Progressive Development)
```

The architecture is intended to keep business logic separate from presentation, support future integrations, and allow the AI assistant to build on reliable financial data.

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Data validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Database migrations | Alembic |
| Web frontend | React, TypeScript, Vite |
| Mobile application | React Native, Expo |
| API communication | REST API |
| Testing | Pytest, Vitest |
| Containers | Docker, Docker Compose |
| Authentication | Token-based authentication |
| Financial data | Provider abstraction and mock provider |
| AI integration | Planned AI service and agent architecture |

Refer to the actual project configuration files for exact dependency versions.

## 5. Project Structure

The following is a conceptual overview. The actual repository structure and module names are authoritative.

```text
DUESWISE-AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── core/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   └── web/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── pages/
│       │   ├── services/
│       │   └── styles/
│       └── package.json
│
├── mobile/
│   ├── app/
│   ├── src/
│   └── package.json
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── database/
│
├── phases/
│   ├── PHASE_1_PROGRESS.md
│   └── PHASE_2_PROGRESS.md
│
├── PROJECT_BLUEPRINT.md
├── CONTRACT.md
├── README.md
└── .env.example
```

## 6. Getting Started

### Prerequisites

Install the following before running the project:

- Python (version compatible with backend requirements)
- Node.js and npm
- PostgreSQL, or Docker with Docker Compose
- Git

### Clone the Repository

```bash
git clone https://github.com/varnesh123/DUESWISE-AI.git
cd DUESWISE-AI
```

### Configure Environment Variables

Create the required environment configuration using the provided example:

```bash
cp .env.example .env
```

On Windows Command Prompt:

```cmd
copy .env.example .env
```

Configure the database connection and other required settings.

Never commit actual secrets or credentials.

### Start the Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the development server using the project's configured entry point. For the standard FastAPI entry point:

```bash
uvicorn app.main:app --reload
```

Backend API documentation:

```text
http://localhost:8000/docs
```

### Start the Web Application

```bash
cd frontend/web
npm install
npm run dev
```

Use the development URL printed by Vite.

### Start the Mobile Application

```bash
cd mobile
npm install
npx expo start
```

Use Expo Go or an appropriate development build to run the application.

### Docker

Where the Docker Compose configuration is available:

```bash
docker compose up --build
```

Use the repository's Docker configuration and environment variables for the actual service setup.

---

## 7. Testing and Quality Assurance

DuesWise uses automated testing to help maintain correctness across its components.

### Backend

From the backend directory:

```bash
python -m pytest -q
```

### Web

From `frontend/web`:

```bash
npm run lint
npm test
npm run build
```

### Mobile

From `mobile`:

```bash
npm run typecheck
```

Run the relevant tests and checks after making changes. Do not assume a feature is complete merely because its implementation exists.

Test results and accepted limitations should be recorded in the corresponding phase progress documents.

---

## 8. Security and Financial Data Principles

Security is an essential engineering requirement because DuesWise handles sensitive financial information. It supports the product's purpose; it is not the product's purpose.

Key principles:

- Enforce authentication and per-user data isolation.
- Validate financial information received from external providers.
- Prevent unauthorized access to another user's financial data.
- Never store bank passwords, UPI PINs, OTPs, or CVVs.
- Use secure handling of authentication tokens.
- Avoid exposing credentials and sensitive information in logs.
- Clearly label mock financial information.
- Never fabricate real account balances or transactions.
- Require explicit user approval before any future payment execution.
- Preserve accurate payment history and auditability.

---

## 9. Development Roadmap

Development is organized into phases. The authoritative scope and acceptance criteria for each phase are maintained in `PROJECT_BLUEPRINT.md`.

| Phase | Focus |
|---|---|
| Phase 1 | Application foundation, authentication, and account/session management |
| Phase 2 | Financial data foundation, accounts, transactions, bills, subscriptions, and dashboards |
| Phase 3 onward | Follow the approved requirements and acceptance criteria in `PROJECT_BLUEPRINT.md` |

The long-term roadmap centers on the intelligent payment assistant, personalized reminders, proactive balance warnings, and approval-based payment assistance.

Phases should be marked complete only after their acceptance criteria and verification requirements have passed.

---

## 10. Development Principles

All future development should follow these principles:

1. Preserve the central DuesWise product vision.
2. Consult `PROJECT_BLUEPRINT.md` before implementing new functionality.
3. Treat the blueprint as a living document and update it when justified.
4. Maintain backward compatibility where practical.
5. Avoid unnecessary rewrites and unrelated scope expansion.
6. Implement required functionality even if an initial plan overlooked it.
7. Keep backend, web, and mobile contracts consistent.
8. Test changes before declaring a phase complete.
9. Never represent mock financial information as real data.
10. Keep the AI assistant and personalized payment management at the center of the product.

---

## 11. Current Project Status

For the latest verified implementation status, refer to:

- `PROJECT_BLUEPRINT.md` — overall project scope and roadmap.
- `phases/PHASE_1_PROGRESS.md` — Phase 1 completion record.
- `phases/PHASE_2_PROGRESS.md` — Phase 2 implementation and verification record.
- Subsequent phase progress documents — later implementation and verification records.

This README describes the project vision and architecture. It should be updated whenever major functionality, setup instructions, or architecture changes.

---

## 12. Contributing

Contributions should preserve the existing architecture and project contracts.

Before submitting changes:

1. Review the relevant section of `PROJECT_BLUEPRINT.md`.
2. Understand the existing implementation.
3. Make focused changes.
4. Run relevant automated checks.
5. Update documentation when necessary.
6. Provide a clear summary of changes and verification results.

Do not commit secrets, environment files, local databases, or generated artifacts.

---

## 13. Project

**DuesWise AI — Intelligent Payment Management Assistant**

Built to help people remember, understand, and manage their financial commitments with intelligent, proactive assistance.

**Repository:** https://github.com/varnesh123/DUESWISE-AI

**Core vision:** One intelligent assistant to keep track of your payments, prepare you for upcoming dues, and help you stay financially organized.
