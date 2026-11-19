"""Deterministic merchant categorisation.

Uses merchant aliases and keyword rules first. Falls back to category ``other``
with a conservative confidence score. The optional AI service (Developer B) is
only consulted for unresolved merchants and never overrides the deterministic
result — see ``ai_client.py``.
"""

import json
import os
import re
from typing import List, Optional, Tuple

_RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "rules")

_DEFAULT_CATEGORY = "other"
_DEFAULT_CONFIDENCE = 0.3


def _load_json(filename: str) -> dict:
    path = os.path.join(_RULES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_aliases_cache: Optional[list] = None
_categories_cache: Optional[dict] = None


def _get_aliases() -> list:
    global _aliases_cache
    if _aliases_cache is None:
        _aliases_cache = _load_json("merchant_aliases.json").get("aliases", [])
    return _aliases_cache


def _get_categories() -> dict:
    global _categories_cache
    if _categories_cache is None:
        _categories_cache = _load_json("categories.json")
    return _categories_cache


def categorise_merchant(
    merchant_raw: str,
    ai_normalized: Optional[str] = None,
    ai_category: Optional[str] = None,
    ai_confidence: Optional[float] = None,
) -> Tuple[str, str, float]:
    """Categorise a merchant deterministically.

    Returns ``(merchant_normalized, category, confidence)``.

    Order of precedence:
      1. Exact/substring match in merchant_aliases.json
      2. Keyword match in categories.json
      3. AI suggestion (only if deterministic resolution is "other")
      4. Default ``other`` with conservative confidence
    """
    raw = (merchant_raw or "").strip()
    raw_upper = raw.upper()

    # 1. Merchant aliases (substring match on uppercased raw merchant)
    for alias in _get_aliases():
        pattern = alias.get("pattern", "").upper()
        if pattern and pattern in raw_upper:
            return (
                alias.get("normalized", raw),
                alias.get("category", _DEFAULT_CATEGORY),
                float(alias.get("confidence", 0.9)),
            )

    # 2. Category keyword rules
    categories = _get_categories().get("categories", {})
    raw_lower = raw.lower()
    for category, keywords in categories.items():
        if category == _DEFAULT_CATEGORY:
            continue
        for kw in keywords:
            if kw.lower() in raw_lower:
                return _clean_name(raw), category, 0.8

    # 3. AI suggestion only when deterministic result is unresolved
    if ai_normalized and ai_category and ai_confidence is not None:
        return ai_normalized, ai_category, min(float(ai_confidence), 0.75)

    # 4. Default
    return _clean_name(raw), _DEFAULT_CATEGORY, _DEFAULT_CONFIDENCE


def _clean_name(raw: str) -> str:
    """Light normalisation: collapse whitespace, title-case short names."""
    cleaned = re.sub(r"\s+", " ", raw).strip()
    # Title-case if it looks like a proper name (all caps or mixed)
    if cleaned.isupper() or len(cleaned) > 25:
        return cleaned
    return cleaned.title()


def categorise_keywords(keywords: List[str]) -> str:
    """Categorise from a list of keyword hints (e.g. from transaction metadata)."""
    cats = _get_categories().get("categories", {})
    joined = " ".join(keywords).lower()
    for category, kws in cats.items():
        if category == _DEFAULT_CATEGORY:
            continue
        for kw in kws:
            if kw.lower() in joined:
                return category
    return _DEFAULT_CATEGORY
