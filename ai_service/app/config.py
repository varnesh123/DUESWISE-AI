"""Environment-driven configuration for the DuesWise AI service.

Both the BLUEPRINT.md names (``AI_*``) and the CONTRACTS.md style names (``LLM_*``)
are accepted so the root ``.env.example`` and this service agree without editing
shared files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parent.parent

_PROVIDER_DISABLED = {"", "none", "disabled", "off", "false"}


class Settings(BaseSettings):
    """Runtime settings. Safe defaults let the service start with no configuration."""

    model_config = SettingsConfigDict(
        env_file=(SERVICE_DIR / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_env: str = "development"
    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("HOST", "AI_SERVICE_HOST"))
    port: int = Field(default=8001, ge=1, le=65535, validation_alias=AliasChoices("PORT", "AI_SERVICE_PORT"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "AI_LOG_LEVEL"))

    ai_provider: str = Field(default="none", validation_alias=AliasChoices("AI_PROVIDER", "LLM_PROVIDER"))
    ai_api_key: str = Field(default="", validation_alias=AliasChoices("AI_API_KEY", "LLM_API_KEY"))
    ai_model: str = Field(default="", validation_alias=AliasChoices("AI_MODEL", "LLM_MODEL"))
    ai_base_url: str = Field(default="", validation_alias=AliasChoices("AI_BASE_URL", "LLM_BASE_URL"))
    ai_timeout_seconds: float = Field(
        default=5.0,
        ge=0.5,
        le=30.0,
        validation_alias=AliasChoices("AI_TIMEOUT_SECONDS", "LLM_TIMEOUT_SECONDS"),
    )
    ai_max_retries: int = Field(
        default=1,
        ge=0,
        le=2,
        validation_alias=AliasChoices("AI_MAX_RETRIES", "LLM_MAX_RETRIES"),
    )

    cors_allow_origins: str = Field(
        default="",
        validation_alias=AliasChoices("CORS_ALLOW_ORIGINS", "ALLOWED_ORIGINS"),
    )

    @property
    def provider_name(self) -> str:
        return (self.ai_provider or "none").strip().lower()

    @property
    def provider_enabled(self) -> bool:
        return self.provider_name not in _PROVIDER_DISABLED

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance (override in tests with cache_clear)."""

    return Settings()
