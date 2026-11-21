"""SQLAlchemy database connection and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _register_models() -> None:
    """Import every model module so ``Base.metadata`` is complete.

    Imports happen lazily to avoid a circular import at module load time
    (each model module imports ``Base`` from this module).
    """
    from app.models import auth_session, business, due, ingestion, nudge  # noqa: F401
    from app.models import scam_alert, subscription, transaction, user  # noqa: F401


def _ensure_columns(table: str, columns: dict[str, str]) -> None:
    """Add missing columns to an existing table.

    ``create_all`` creates new tables but never alters existing ones. This
    lightweight, idempotent upgrade keeps existing local databases usable after
    new nullable/defaulted columns are introduced, without a migration tool.
    """
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table)}
    missing = [(name, ddl) for name, ddl in columns.items() if name not in existing]
    if not missing:
        return
    with engine.begin() as connection:
        for name, ddl in missing:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    """Create tables and apply additive, backwards-compatible upgrades.

    This is repeatable and safe to run on every application startup. Existing
    rows are preserved; only new nullable/defaulted columns are added.
    """
    _register_models()
    Base.metadata.create_all(bind=engine)
    _ensure_columns(
        "users",
        {
            "password_hash": "VARCHAR(255)",
            "is_demo": "BOOLEAN NOT NULL DEFAULT 0",
        },
    )


def get_db() -> Session:
    """Yield a database session, commit on success, and guarantee cleanup.

    Intended for use with ``fastapi.Depends``.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
