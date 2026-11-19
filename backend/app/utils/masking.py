"""Masking helpers for financial identifiers — never expose full account numbers."""

import re


def mask_account_number(account: str) -> str:
    """Mask an account number, showing only the last 4 digits.

    Examples:
        "123456789012" -> "XXXXXXXX9012"
        "XX1234"       -> "XX1234" (already masked)
    """
    if not account:
        return ""
    digits = re.sub(r"\D", "", account)
    if not digits:
        return account
    if len(digits) <= 4:
        return account
    return "X" * (len(digits) - 4) + digits[-4:]


def mask_upi_handle(upi: str) -> str:
    """Mask a UPI handle, preserving the bank/domain part.

    Example: "ravi.okhdfcbank@ybl" -> "rXXXXXX@ybl"
    """
    if not upi or "@" not in upi:
        return upi or ""
    handle, bank = upi.rsplit("@", 1)
    if not handle:
        return f"@{bank}"
    if len(handle) <= 2:
        masked = "X" * len(handle)
    else:
        masked = handle[0] + "X" * (len(handle) - 2) + handle[-1]
    return f"{masked}@{bank}"
