"""Optional HTTP client for Developer B's AI service.

The backend must continue working when the AI service is unavailable.
This client is used only for merchant normalisation (and, later, scam
explanations / nudge wording). It never performs financial calculations.

Rules enforced here:
- Short, configurable timeout (default 5s).
- Maximum one retry.
- Graceful failure: returns None on any error, never raises to callers.
- Validates the AI response shape before returning.
- Never sends unmasked account identifiers, OTPs, PINs or credentials.
"""

import httpx
from typing import Optional, Dict, Any

from app.config import settings


class AIClient:
    """Thin wrapper around the AI service HTTP JSON endpoints."""

    def __init__(self) -> None:
        self.base_url = settings.AI_SERVICE_BASE_URL.rstrip("/")
        self.timeout = settings.AI_TIMEOUT_SECONDS
        self.max_retries = settings.AI_MAX_RETRIES
        self.enabled = settings.AI_ENABLED

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "Accept": "application/json"}

    def _validate_merchant_normalize_response(self, payload: Any) -> Optional[Dict[str, Any]]:
        """Validate the merchant-normalize response schema."""
        if not isinstance(payload, dict):
            return None
        normalized = payload.get("merchant_normalized")
        category = payload.get("category")
        confidence = payload.get("confidence")
        if not isinstance(normalized, str) or not normalized:
            return None
        if not isinstance(category, str) or not category:
            return None
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            return None
        return {
            "merchant_normalized": normalized,
            "category": category,
            "confidence": float(confidence),
        }

    def merchant_normalize(
        self, merchant_raw: str, currency: str = "INR"
    ) -> Optional[Dict[str, Any]]:
        """Ask the AI service to normalise a merchant name.

        Returns a dict with merchant_normalized/category/confidence, or None
        if the service is disabled, unavailable, or returns an invalid shape.
        Never raises to the caller.
        """
        if not self.enabled:
            return None

        url = f"{self.base_url}/api/v1/ai/merchant-normalize"
        payload = {"merchant_raw": merchant_raw, "currency": currency}

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=self._headers())
                    if response.status_code != 200:
                        last_error = Exception(f"HTTP {response.status_code}")
                        continue
                    validated = self._validate_merchant_normalize_response(response.json())
                    if validated is not None:
                        return validated
                    last_error = Exception("Invalid AI response schema")
            except Exception as exc:  # noqa: BLE001 - swallow all, return None
                last_error = exc
                continue

        # Service unavailable or invalid — caller uses deterministic fallback.
        return None
