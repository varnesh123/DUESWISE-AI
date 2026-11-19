# DUESWISE — API CONTRACTS

**Document status:** Draft — Requires approval from Developer A and Developer B  
**API version:** v1  
**Base backend URL:** `http://localhost:8000`  
**Base AI service URL:** `http://localhost:8001`

---

## 1. Purpose

This document defines the communication contract between:

1. Main Backend — Developer A
2. Independent AI Service — Developer B
3. Flutter Mobile Application — Developer B

All developers must follow these API definitions.

Changes require agreement from both developers.

## 2. Global conventions

### 2.1 JSON conventions

- JSON field names must use snake_case.
- All API responses must return JSON unless explicitly documented otherwise.
- All monetary values must use integer paise.
- Currency defaults to INR.
- Dates must use `YYYY-MM-DD`.
- Timestamps must use ISO-8601 with timezone information.
- Boolean fields must use true or false.
- Optional fields must explicitly document whether null is allowed.

### 2.2 Money representation

Example:

- ₹100 = 10000 paise.
- ₹1,000 = 100000 paise.
- ₹10,000 = 1000000 paise.

Never use floating-point numbers for financial calculations.

### 2.3 Standard error format

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": {}
  }
}

## 3. Authentication

Authentication method: Bearer token.

Protected endpoints must receive:

Authorization: Bearer <access_token>

Public endpoints:
- POST /api/v1/auth/register
- POST /api/v1/auth/login

Developer A must specify the token format, expiry and refresh mechanism.

## 4. Main Backend API

Base URL: `http://localhost:8000`

### 4.1 Authentication

POST /api/v1/auth/register

POST /api/v1/auth/login

Developer A must finalise request and response schemas.

### 4.2 Dashboard

GET /api/v1/dashboard/summary

Example response:

{
  "currency": "INR",
  "available_balance_paise": 3200000,
  "safe_to_spend_paise": 845000,
  "upcoming_dues_total_paise": 2000000,
  "safety_reserve_paise": 355000,
  "calculated_until": "2026-11-25",
  "data_confidence": "high"
}

### 4.3 Transactions

GET /api/v1/transactions

POST /api/v1/transactions/ingest

Transaction fields:

- id
- amount_paise
- currency
- transaction_type
- merchant_raw
- merchant_normalized
- category
- payment_method
- transaction_date
- source
- confidence

### 4.4 Dues

GET /api/v1/dues

Fields:

- id
- title
- due_type
- amount_paise
- due_date
- status
- is_mandatory
- confidence

### 4.5 Subscriptions

GET /api/v1/subscriptions

Fields:

- id
- merchant
- category
- expected_amount_paise
- frequency
- next_due_date
- detection_confidence
- status
- is_user_confirmed

### 4.6 Nudges

GET /api/v1/nudges

Fields:

- id
- type
- priority
- title
- message
- created_at
- read

### 4.7 Scam alerts

GET /api/v1/scam-alerts

POST /api/v1/scam-alerts/analyze

Fields:

- id
- risk_score
- risk_level
- verdict
- indicators
- explanation
- status

### 4.8 Tax comparison

POST /api/v1/tax/compare

Request and response schemas must include:

- financial_year
- annual_income_paise
- deductions_paise
- old_regime
- new_regime
- recommended_lower_tax_regime
- estimated_difference_paise

Developer A must define the complete calculation input and output schema and verify the applicable tax rules.

### 4.9 Small-business cash flow

GET /api/v1/business/cashflow

Developer A must define fields for:

- sales
- expenses
- receivables
- payables
- projected_cash_balance_paise

### 4.10 Investment summary

GET /api/v1/investments/summary

This is a simulated educational feature. It must not execute real investments or trades.

Developer A must define the complete response schema.

## 5. Independent AI Service

Base URL: `http://localhost:8001`

### 5.1 Merchant normalisation

POST /api/v1/ai/merchant-normalize

Request:

{
  "merchant_raw": "NETFLIX INDIA",
  "currency": "INR"
}

Response:

{
  "merchant_normalized": "Netflix",
  "category": "entertainment",
  "confidence": 0.96
}

### 5.2 Scam explanation

POST /api/v1/ai/explain-scam

Request and response schemas must be finalised by Developer B.

The deterministic backend remains responsible for calculating the risk score.

### 5.3 Nudge generation

POST /api/v1/ai/generate-nudge

Request and response schemas must be finalised by Developer B.

The backend decides whether a nudge is eligible. AI only generates its wording.

## 6. Enums

Initial proposed values:

### Transaction type
- credit
- debit

### Payment method
- UPI
- card
- bank_transfer
- cash
- other

### Risk level
- low
- medium
- high
- critical

### Due status
- upcoming
- due
- paid
- overdue

### Subscription status
- active
- cancelled
- paused
- uncertain

Developer A and Developer B must approve the final enum values.

## 7. API versioning

All endpoints must begin with `/api/v1/`.

Breaking changes require a jointly approved contract update.

## 8. Integration rules

1. Flutter communicates with the main backend using HTTP JSON.
2. The backend communicates with the AI service using HTTP JSON.
3. Flutter must not import backend Python modules.
4. AI service must not import backend ORM or database models.
5. Flutter must support mock and live repository implementations.
6. Mock mode must remain available throughout the hackathon.
7. AI service failure must not break core financial calculations.
8. All financial calculations remain deterministic.

## 9. Contract approval

Developer A must confirm the main backend endpoint definitions.

Developer B must confirm the AI service endpoint definitions and Flutter integration requirements.

**Status: Draft. Do not treat incomplete endpoint schemas as final until both developers approve them.**

---

## 10. As-built implementation notes

The repository now contains a working backend, Flutter client and AI service. A few
endpoints were implemented differently from the draft above (demo sessions instead of
password login, `/scams` instead of `/scam-alerts`, `POST /dues/{id}/mark-paid`,
unified `POST /transactions/ingest`). The running behaviour, request/response shapes
and the full app-to-backend mapping are documented in
[`docs/API_INTEGRATION.md`](docs/API_INTEGRATION.md). Where this draft and the
implementation disagree, that document describes the system as built.