"""Environment-based application configuration.

Settings are read from environment variables with safe development defaults.
Never commit real secrets to this file or to `.env`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Each field is overridable through an environment variable of the same name.
    """

    DATABASE_URL: str = "sqlite:///./dueswise.db"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    APP_NAME: str = "DuesWise"
    APP_VERSION: str = "1.0.0"

    # AI service integration (Developer B). Optional and gracefully degraded.
    AI_SERVICE_BASE_URL: str = "http://localhost:8001"
    AI_TIMEOUT_SECONDS: int = 5
    AI_MAX_RETRIES: int = 1
    AI_ENABLED: bool = False

    DEFAULT_CURRENCY: str = "INR"
    TIMEZONE: str = "Asia/Kolkata"
    FORECAST_HORIZON_DAYS: int = 30
    SAFETY_RESERVE_PERCENT: int = 10
    MAX_NUDGES_PER_7_DAYS: int = 3
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE_MB: int = 10

    # Real account sessions (opaque bearer tokens, hashed at rest).
    SESSION_TTL_MINUTES: int = 60 * 24 * 7

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
