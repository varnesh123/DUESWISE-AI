"""Tests for database initialisation and session lifecycle."""

from sqlalchemy import inspect, text

from app.database import Base, engine as app_engine, init_db
from app.models.user import User


def test_init_db_creates_tables():
    """init_db() should create all tables defined on the model metadata."""
    init_db()
    inspector = inspect(app_engine)
    table_names = set(inspector.get_table_names())
    assert "users" in table_names


def test_users_table_has_expected_columns():
    """The users table should contain the agreed columns."""
    inspector = inspect(app_engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    expected = {
        "id",
        "name",
        "email",
        "persona",
        "currency",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_database_session_lifecycle(db_session):
    """A database session can be opened, used, and closed cleanly."""
    count = db_session.query(User).count()
    assert count == 0
    db_session.add(User(name="Demo User", persona="salaried"))
    db_session.flush()
    assert db_session.query(User).count() == 1


def test_database_connectivity_reported_ok(client):
    """Database connectivity should be reported as 'ok' via system status."""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"
