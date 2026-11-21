"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.config import settings
from app.database import Base, init_db  # noqa: F401  (Base imported for metadata registration)
from app.schemas.common import ErrorDetail, ErrorResponse
from app.utils.logging import setup_logging

# Import all models so Base.metadata registers every table before create_all().
from app.models.user import User  # noqa: F401
from app.models.auth_session import AuthSession  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.ingestion import IngestionRecord  # noqa: F401
from app.models.due import Due  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.nudge import Nudge  # noqa: F401
from app.models.scam_alert import ScamAlert  # noqa: F401
from app.models.business import BusinessEntry  # noqa: F401

setup_logging(level=settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialise the database on application startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(api_router)


def _error_code_for_status(status_code: int) -> str:
    """Map an HTTP status code to a contract error code."""
    mapping = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "DUPLICATE_RESOURCE",
        405: "METHOD_NOT_ALLOWED",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_FILE_TYPE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        503: "AI_SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, "INTERNAL_ERROR")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with the standard contract error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=_error_code_for_status(exc.status_code),
                message=str(exc.detail),
                details={},
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with the standard contract format."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": exc.errors()},
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected errors without leaking internal details."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={},
            )
        ).model_dump(),
    )
