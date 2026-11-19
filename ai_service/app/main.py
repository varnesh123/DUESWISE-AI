"""FastAPI application for the DuesWise independent AI service."""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routes import ai_router
from app.config import get_settings
from app.services.llm_provider import build_provider

logger = logging.getLogger("dueswise.ai")


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="DuesWise AI Service",
        version=__version__,
        description=(
            "Advisory AI microservice for merchant normalisation, scam explanations and nudge wording. "
            "Authoritative financial calculations remain in the DuesWise backend."
        ),
        docs_url="/docs",
        redoc_url=None,
    )

    if settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        # Log only request metadata. Bodies are never logged.
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration_ms)
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in error.get("loc", ())],
                "msg": str(error.get("msg", "invalid value")),
                "type": str(error.get("type", "value_error")),
            }
            for error in exc.errors()
        ]
        # Deliberately omit the offending input so secrets are not echoed back.
        return _error_response(422, "VALIDATION_ERROR", "Invalid request payload.", {"errors": errors})

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _error_response(exc.status_code, code, message)

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces, exception text or request content to clients.
        logger.error("Unhandled error while processing %s: %s", request.url.path, type(exc).__name__)
        return _error_response(500, "INTERNAL_ERROR", "An internal error occurred.")

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])

    provider = build_provider(settings)
    logger.info(
        "DuesWise AI service ready (env=%s, llm_provider=%s, llm_enabled=%s)",
        settings.app_env,
        provider.name,
        provider.enabled,
    )
    if not provider.enabled:
        logger.info("Deterministic fallbacks active; no external LLM will be called")

    return application


app = create_app()
