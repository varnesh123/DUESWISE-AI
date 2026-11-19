"""Unit tests for transaction repository — user-scoping, dedup, CRUD."""

from datetime import date

import pytest
from app.repositories.transaction_repository import TransactionRepository
from app.models.user import User
from app.models.transaction import Transaction


@pytest.fixture
def repo(db_session):
    # Create a demo user
    user = User(id="11111111-1111-4111-8111-111111111111", name="Test User", persona="salaried")
    db_session.add(user)
    db_session.flush()
    return TransactionRepository(db_session), user


def test_create_and_get(repo):
    repository, user = repo
    txn = repository.create(
        user_id=user.id,
        amount_paise=49900,
        currency="INR",
        transaction_type="debit",
        merchant_raw="NETFLIX",
        merchant_normalized="Netflix",
        category="entertainment",
        payment_method="upi",
        transaction_date=date(2026, 11, 18),
        source="sms",
        confidence=0.96,
    )
    assert txn.id is not None
    assert txn.user_id == user.id

    fetched = repository.get(txn.id, user.id)
    assert fetched is not None
    assert fetched.amount_paise == 49900
    assert fetched.merchant_normalized == "Netflix"


def test_get_nonexistent_returns_none(repo):
    repository, user = repo
    assert repository.get("00000000-0000-0000-0000-000000000000", user.id) is None


def test_user_scoping(repo):
    repository, user = repo
    repository.create(
        user_id=user.id,
        amount_paise=1000,
        transaction_type="debit",
        merchant_raw="A",
        merchant_normalized="A",
        category="other",
        payment_method="upi",
        transaction_date=date(2026, 11, 18),
        source="sms",
    )
    # Another user should not see this transaction
    other_txns, _ = repository.list(user_id="99999999-9999-9999-9999-999999999999")
    assert len(other_txns) == 0

    user_txns, total = repository.list(user_id=user.id)
    assert total == 1


def test_duplicate_prevention_by_fingerprint(repo):
    repository, user = repo
    repository.create(
        user_id=user.id,
        amount_paise=49900,
        transaction_type="debit",
        merchant_raw="NETFLIX",
        merchant_normalized="Netflix",
        category="entertainment",
        payment_method="upi",
        transaction_date=date(2026, 11, 18),
        source="sms",
    )
    dup = repository.find_duplicate(
        user_id=user.id,
        amount_paise=49900,
        transaction_date=date(2026, 11, 18),
        transaction_type="debit",
        merchant_normalized="Netflix",
        payment_method="upi",
        source="sms",
    )
    assert dup is not None

    # Different amount should not be a duplicate
    not_dup = repository.find_duplicate(
        user_id=user.id,
        amount_paise=99900,
        transaction_date=date(2026, 11, 18),
        transaction_type="debit",
        merchant_normalized="Netflix",
        payment_method="upi",
        source="sms",
    )
    assert not_dup is None


def test_duplicate_prevention_by_source_reference(repo):
    repository, user = repo
    repository.create(
        user_id=user.id,
        amount_paise=49900,
        transaction_type="debit",
        merchant_raw="NETFLIX",
        merchant_normalized="Netflix",
        category="entertainment",
        payment_method="upi",
        transaction_date=date(2026, 11, 18),
        source="sms",
        source_reference="REF-123",
    )
    dup = repository.find_duplicate(
        user_id=user.id,
        amount_paise=99900,  # different amount
        transaction_date=date(2026, 11, 20),  # different date
        transaction_type="credit",  # different type
        merchant_normalized="Other",  # different merchant
        payment_method="card",
        source="sms",
        source_reference="REF-123",  # same reference
    )
    assert dup is not None


def test_list_pagination_and_filters(repo):
    repository, user = repo
    for i in range(5):
        repository.create(
            user_id=user.id,
            amount_paise=1000 * (i + 1),
            transaction_type="debit",
            merchant_raw=f"Merchant {i}",
            merchant_normalized=f"Merchant {i}",
            category="entertainment" if i % 2 == 0 else "groceries",
            payment_method="upi",
            transaction_date=date(2026, 11, i + 1),
            source="sms",
        )

    items, total = repository.list(user_id=user.id, page=1, page_size=3)
    assert total == 5
    assert len(items) == 3

    items, total = repository.list(user_id=user.id, category="groceries")
    assert total == 2

    items, total = repository.list(user_id=user.id, transaction_type="credit")
    assert total == 0
