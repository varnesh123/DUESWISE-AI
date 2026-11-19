"""SQLAlchemy database connection and session management."""

from sqlalchemy import create_engine
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


def init_db() -> None:
    """Create all database tables defined on the model metadata.

    This is repeatable and safe to run on every application startup.
    """
    Base.metadata.create_all(bind=engine)


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
