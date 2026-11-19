"""Monetary helpers — integer paise only, never floating-point for money."""

import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def to_paise(amount) -> int:
    """Convert a rupee amount (int, Decimal, or string) to integer paise.

    Never uses floating-point arithmetic. Accepts rupee symbols, commas,
    spaces and the 'Rs' / '₹' prefixes common in Indian SMS/bank statements.
    """
    if isinstance(amount, bool):
        raise ValueError(f"Invalid amount: {amount!r}")
    if isinstance(amount, int):
        return amount
    if isinstance(amount, Decimal):
        try:
            return int((amount * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        except InvalidOperation:
            raise ValueError(f"Cannot parse amount: {amount!r}")

    amount_str = str(amount).strip()
    if not amount_str:
        raise ValueError("Amount cannot be empty")

    # Remove currency symbols/prefixes first so "Rs.499" -> "499" (the period
    # after "Rs" is not a decimal separator).
    amount_str = re.sub(r"(?i)(₹|rs\.?|inr)\s*", "", amount_str)

    # Keep only digits, dot and minus sign; drop commas, spaces, etc.
    cleaned = re.sub(r"[^0-9.\-]", "", amount_str)
    if cleaned in ("", "-", ".", "-.", "+"):
        raise ValueError(f"Cannot parse amount: {amount!r}")

    if cleaned.count(".") > 1:
        raise ValueError(f"Cannot parse amount: {amount!r}")

    if "." in cleaned:
        rupees_part, paise_part = cleaned.split(".", 1)
        paise_part = (paise_part + "00")[:2]
    else:
        rupees_part = cleaned
        paise_part = "00"

    if rupees_part in ("", "-", "+"):
        rupees_part = "0"

    try:
        rupees = int(rupees_part)
        paise = int(paise_part)
    except ValueError:
        raise ValueError(f"Cannot parse amount: {amount!r}")

    total_paise = rupees * 100 + paise
    if total_paise < 0:
        raise ValueError(f"Amount cannot be negative: {amount!r}")
    return total_paise


def paise_to_rupees(paise: int) -> str:
    """Format integer paise as a rupee string for display only (not calculation)."""
    rupees = abs(paise) // 100
    remaining_paise = abs(paise) % 100
    sign = "-" if paise < 0 else ""
    return f"{sign}₹{rupees}.{remaining_paise:02d}"


def validate_amount_paise(paise: int) -> None:
    """Validate that a monetary value is a non-negative integer in paise."""
    if not isinstance(paise, int) or isinstance(paise, bool):
        raise ValueError("Amount must be an integer in paise")
    if paise < 0:
        raise ValueError("Amount cannot be negative")
