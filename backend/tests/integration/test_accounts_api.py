"""Integration tests for real accounts, sessions, and ownership isolation."""

import time

from app.models.auth_session import AuthSession
from app.models.user import User
from app.security.sessions import hash_session_token


def _register(client, email="user@example.com", password="correct-horse", name="Test User"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_real_account_and_session(client, db_session):
    body = _register(client, email="  User@Example.COM ", name="Asha")

    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["name"] == "Asha"
    assert body["user"]["is_demo"] is False
    assert body["token_type"] == "bearer"
    assert body["expires_in_minutes"] > 0
    # A real session token must not be the user's UUID.
    assert body["access_token"] != body["user_id"]

    user = db_session.query(User).filter(User.id == body["user_id"]).first()
    assert user is not None
    assert user.password_hash is not None
    assert "correct-horse" not in user.password_hash
    assert user.password_hash.startswith("pbkdf2_sha256$")

    me = client.get("/api/v1/auth/me", headers=_headers(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_register_rejects_duplicate_email_case_insensitively(client):
    _register(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Other", "email": "DUP@example.com", "password": "another-pass"},
    )
    assert response.status_code == 409


def test_register_validates_email_and_password(client):
    bad_email = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "not-an-email", "password": "long-enough"},
    )
    assert bad_email.status_code == 422

    short_password = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "a@example.com", "password": "short"},
    )
    assert short_password.status_code == 422


def test_login_success_and_failure(client):
    _register(client, email="login@example.com", password="my-secret-pass")

    ok = client.post(
        "/api/v1/auth/login",
        json={"email": "LOGIN@example.com", "password": "my-secret-pass"},
    )
    assert ok.status_code == 200
    token = ok.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers=_headers(token)).status_code == 200

    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrong-password"},
    )
    assert wrong.status_code == 401

    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "my-secret-pass"},
    )
    assert unknown.status_code == 401


def test_logout_revokes_only_the_current_session(client):
    first = _register(client, email="logout@example.com")["access_token"]
    second = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "correct-horse"},
    ).json()["access_token"]

    assert client.post("/api/v1/auth/logout", headers=_headers(first)).status_code == 204
    assert client.get("/api/v1/auth/me", headers=_headers(first)).status_code == 401
    # A second signed-in device remains valid.
    assert client.get("/api/v1/auth/me", headers=_headers(second)).status_code == 200


def test_expired_session_is_rejected(client, db_session):
    body = _register(client, email="expired@example.com")
    raw_token = "expired-session-token"
    db_session.add(
        AuthSession(
            user_id=body["user_id"],
            token_hash=hash_session_token(raw_token),
            expires_at=int(time.time()) - 1,
        )
    )
    db_session.flush()

    response = client.get("/api/v1/auth/me", headers=_headers(raw_token))
    assert response.status_code == 401


def test_records_are_isolated_between_accounts(client):
    alice = _register(client, email="alice@example.com", name="Alice")
    bob = _register(client, email="bob@example.com", name="Bob")
    alice_headers = _headers(alice["access_token"])
    bob_headers = _headers(bob["access_token"])

    due = client.post(
        "/api/v1/dues",
        json={
            "title": "Alice rent",
            "due_type": "rent",
            "amount_paise": 1500000,
            "due_date": "2026-12-01",
            "frequency": "monthly",
            "is_mandatory": True,
        },
        headers=alice_headers,
    )
    assert due.status_code == 201
    due_id = due.json()["id"]

    txn = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 50000,
            "transaction_type": "debit",
            "merchant": "Alice cafe",
            "category": "food",
            "payment_method": "upi",
            "transaction_date": "2026-11-20",
        },
        headers=alice_headers,
    )
    assert txn.status_code == 201
    txn_id = txn.json()["id"]

    # Bob sees an empty account.
    assert client.get("/api/v1/dues", headers=bob_headers).json()["total"] == 0
    assert client.get("/api/v1/transactions", headers=bob_headers).json()["total"] == 0

    # Bob cannot read, update, delete, or mark paid any of Alice's records.
    assert client.get(f"/api/v1/dues/{due_id}", headers=bob_headers).status_code == 404
    assert client.patch(
        f"/api/v1/dues/{due_id}",
        json={"amount_paise": 1},
        headers=bob_headers,
    ).status_code == 404
    assert client.delete(f"/api/v1/dues/{due_id}", headers=bob_headers).status_code == 404
    assert client.post(
        f"/api/v1/dues/{due_id}/mark-paid",
        json={"paid_date": "2026-11-21"},
        headers=bob_headers,
    ).status_code == 404

    assert client.get(
        f"/api/v1/transactions/{txn_id}", headers=bob_headers
    ).status_code == 404
    assert client.patch(
        f"/api/v1/transactions/{txn_id}",
        json={"amount_paise": 1},
        headers=bob_headers,
    ).status_code == 404
    assert client.delete(
        f"/api/v1/transactions/{txn_id}", headers=bob_headers
    ).status_code == 404

    # Alice can still see her records.
    assert client.get("/api/v1/dues", headers=alice_headers).json()["total"] == 1
    assert client.get("/api/v1/transactions", headers=alice_headers).json()["total"] == 1


def test_due_edit_and_delete(client):
    body = _register(client, email="dues@example.com")
    headers = _headers(body["access_token"])

    created = client.post(
        "/api/v1/dues",
        json={
            "title": "Old title",
            "due_type": "utility",
            "amount_paise": 10000,
            "due_date": "2026-12-05",
            "frequency": "one_time",
            "is_mandatory": False,
        },
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/v1/dues/{created['id']}",
        json={
            "title": "New title",
            "due_type": "rent",
            "frequency": "monthly",
            "amount_paise": 20000,
            "is_mandatory": True,
        },
        headers=headers,
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["title"] == "New title"
    assert payload["due_type"] == "rent"
    assert payload["frequency"] == "monthly"
    assert payload["amount_paise"] == 20000
    assert payload["is_mandatory"] is True

    deleted = client.delete(f"/api/v1/dues/{created['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/dues/{created['id']}", headers=headers).status_code == 404


def test_transaction_edit_and_delete(client):
    body = _register(client, email="txns@example.com")
    headers = _headers(body["access_token"])

    created = client.post(
        "/api/v1/transactions/manual",
        json={
            "amount_paise": 19900,
            "transaction_type": "debit",
            "merchant": "Old merchant",
            "category": "other",
            "payment_method": "upi",
            "transaction_date": "2026-11-19",
        },
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/v1/transactions/{created['id']}",
        json={
            "amount_paise": 29900,
            "merchant": "New merchant",
            "category": "groceries",
            "transaction_date": "2026-11-20",
            "description": "Edited entry",
        },
        headers=headers,
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["amount_paise"] == 29900
    assert payload["merchant_raw"] == "New merchant"
    assert payload["merchant_normalized"] == "New merchant"
    assert payload["category"] == "groceries"
    assert payload["transaction_date"] == "2026-11-20"
    assert payload["description"] == "Edited entry"

    deleted = client.delete(f"/api/v1/transactions/{created['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(
        f"/api/v1/transactions/{created['id']}", headers=headers
    ).status_code == 404


def test_empty_dashboard_for_new_account(client):
    body = _register(client, email="empty@example.com")
    response = client.get(
        "/api/v1/dashboard/summary",
        headers=_headers(body["access_token"]),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["available_balance_paise"] == 0
    assert payload["safe_to_spend_paise"] == 0
    assert payload["recent_transactions"] == []
    assert payload["next_due"] is None
