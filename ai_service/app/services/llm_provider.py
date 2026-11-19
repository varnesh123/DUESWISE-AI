"""LLM provider abstraction.

Providers return a parsed JSON object or ``None``. They never raise provider
errors to the API layer and never log prompt/response content.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Protocol, runtime_checkable

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
}
SUPPORTED_PROVIDERS = {"openai_compatible", "openai", "groq"}
MAX_ALLOWED_RETRIES = 1


@runtime_checkable
class LLMProvider(Protocol):
    enabled: bool
    name: str

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict | None:
        """Return a validated-shape JSON object, or None when unavailable."""


class DisabledLLMProvider:
    """No-op provider used when ``AI_PROVIDER=none`` or configuration is incomplete."""

    enabled = False
    name = "none"

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict | None:
        return None


def _parse_json_object(content: str) -> dict | None:
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


class OpenAICompatibleProvider:
    """Minimal HTTP JSON chat-completions client with timeout and one retry."""

    enabled = True

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 5.0,
        max_retries: int = 1,
        name: str = "openai_compatible",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.name = name
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, min(max_retries, MAX_ALLOWED_RETRIES))
        self._transport = transport

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict | None:
        payload = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"
        attempts = 1 + self._max_retries

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds, transport=self._transport) as client:
                    response = client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                logger.warning("LLM request failed on attempt %s: %s", attempt, type(exc).__name__)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                logger.warning("LLM provider returned status %s on attempt %s", response.status_code, attempt)
                continue
            if response.status_code >= 400:
                logger.warning("LLM provider rejected the request with status %s", response.status_code)
                return None

            try:
                body = response.json()
                content = body["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                logger.warning("LLM response could not be read: %s", type(exc).__name__)
                return None

            return _parse_json_object(content) if isinstance(content, str) else None

        return None


def build_provider(settings: Settings | None = None) -> LLMProvider:
    """Build the configured provider, falling back to disabled on bad config."""

    settings = settings or get_settings()
    provider_name = settings.provider_name

    if not settings.provider_enabled:
        return DisabledLLMProvider()
    if provider_name not in SUPPORTED_PROVIDERS:
        logger.warning("Unknown AI_PROVIDER configured; deterministic mode enabled")
        return DisabledLLMProvider()

    api_key = settings.ai_api_key.strip()
    model = settings.ai_model.strip()
    if not api_key or not model:
        logger.warning("LLM provider requested without credentials or model; deterministic mode enabled")
        return DisabledLLMProvider()

    base_url = settings.ai_base_url.strip() or DEFAULT_BASE_URLS.get(provider_name, "")
    if not base_url:
        logger.warning("LLM base URL is missing; deterministic mode enabled")
        return DisabledLLMProvider()

    return OpenAICompatibleProvider(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout_seconds=settings.ai_timeout_seconds,
        max_retries=settings.ai_max_retries,
        name=provider_name,
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    """FastAPI dependency; tests override this and never reach the network."""

    return build_provider()


def clear_provider_cache() -> None:
    get_llm_provider.cache_clear()
