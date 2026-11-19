"""System status endpoint.

GET /api/v1/system/status reports basic system information without exposing
secrets, credentials, or local filesystem paths.
"""

from sqlalchemy import text
from fastapi import APIRouter

from app.config import settings
from app.database import engine
from app.schemas.system import SystemStatus

router = APIRouter()


@router.get(
    "/system/status",
    response_model=SystemStatus,
    tags=["system"],
    summary="System status",
)
def system_status() -> SystemStatus:
    """Return application name, version, environment and database status."""
    database = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database = "error"

    return SystemStatus(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database=database,
    )
