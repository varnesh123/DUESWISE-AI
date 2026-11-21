"""Health endpoint.

GET /health reports that the API process is running.
"""

from fastapi import APIRouter

from app.schemas.system import HealthResponse

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
)
def health() -> HealthResponse:
    "Return API process health."
    return HealthResponse(status="ok")


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
)
def health_v2() -> HealthResponse:
    "Return API process health."
    return HealthResponse(status="ok")
