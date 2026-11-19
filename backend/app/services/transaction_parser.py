"""SMS-style transaction parser.

Deterministic, regex-based parsing of Indian bank/UPI SMS messages.
No LLM involvement. Supports UPI, card, net banking, IMPS, NEFT, ATM and
bank transfer formats with rupee symbols, commas and common bank wording.

Raises SmsParseError when a message cannot be recognised as a transaction —
callers must return a documented parsing error, never a fabricated transaction.
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.utils.dates import parse_indian_date
from app.utils.money import to_paise


class SmsParseError(Exception):
    """Raised when an SMS message cannot be parsed as a transaction."""


@dataclass
class ParsedTransaction:
    amount_paise: int
    transaction_type: str  # credit / debit
    merchant_raw: str
    transaction_date: date
    payment_method: str  # upi / card / net_banking / imps / neft / atm / other
    payment_gateway: Optional[str]
    source_reference: Optional[str]
    confidence: float
    description: Optional[str]


# Keywords that indicate money OUT vs money IN
_DEBIT_KEYWORDS = ("debited", "withdrawal", "spent", "paid", "payment", "debited from")
_CREDIT_KEYWORDS = ("credited", "credit", "received", "deposit", "refund")

_GATEWAY_HINTS = {
    "gpay": "gpay",
    "google pay": "gpay",
    "phonepe": "phonepe",
    "paytm": "paytm",
    "bhim": "bhim",
    "amazongpay": "gpay",
}


def _detect_type(message: str) -> str:
    low = message.lower()
    for kw in _DEBIT_KEYWORDS:
        if kw in low:
            return "debit"
    for kw in _CREDIT_KEYWORDS:
        if kw in low:
            return "credit"
    return "debit"  # conservative default for money movement messages


def _detect_payment_method(message: str) -> str:
    low = message.lower()
    if "upi" in low:
        return "upi"
    if "imps" in low:
        return "imps"
    if "neft" in low:
        return "neft"
    if "atm" in low:
        return "atm"
    if "card" in low:
        return "card"
    if "net banking" in low or "internet banking" in low:
        return "net_banking"
    if "transfer" in low:
        return "net_banking"
    return "other"


def _detect_gateway(message: str) -> Optional[str]:
    low = message.lower()
    for hint, gateway in _GATEWAY_HINTS.items():
        if hint in low:
            return gateway
    return None


def _extract_reference(message: str) -> Optional[str]:
    """Try common reference patterns: UPI Ref, Ref, UTR, Ref No."""
    patterns = [
        r"(?i)UPI\s*Ref\s*[:\-]?\s*([A-Z0-9]{6,})",
        r"(?i)Ref\s*[:\-]?\s*([A-Z0-9]{6,})",
        r"(?i)UTR\s*[:\-]?\s*([A-Z0-9]{6,})",
        r"(?i)Ref\s*No\s*[:\-]?\s*([A-Z0-9]{6,})",
    ]
    for pat in patterns:
        m = re.search(pat, message)
        if m:
            return m.group(1)
    return None


def _clean_merchant(raw: str) -> str:
    """Trim trailing noise from an extracted merchant name."""
    raw = raw.strip()
    # Remove common trailing tokens
    for token in ("on", "at", "via", "from", "to", "for", "of", "Ref", "ref", "UTR", "Balance", "Avl", "Avail"):
        raw = re.sub(rf"\s+{re.escape(token)}\b.*$", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"[.,;:!]+$", "", raw).strip()
    return raw


def _extract_amount(message: str) -> int:
    """Find the first currency amount in the message and convert to paise."""
    patterns = [
        r"(?:₹|Rs\.?|INR)\s*([\d,]+\.?\d*)",
        r"([\d,]+\.?\d*)\s*(?:rupee|rs|inr)",
    ]
    for pat in patterns:
        m = re.search(pat, message, flags=re.IGNORECASE)
        if m:
            return to_paise(m.group(1))
    raise SmsParseError("No amount found in message")


def _extract_date(message: str) -> date:
    """Find the first Indian/ISO date in the message."""
    patterns = [
        r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pat in patterns:
        m = re.search(pat, message)
        if m:
            return parse_indian_date(m.group(1))
    raise SmsParseError("No date found in message")


def _extract_merchant_upi(message: str, trans_type: str) -> str:
    """Extract merchant/payee from a UPI message."""
    if trans_type == "debit":
        # "for UPI payment to NETFLIX INDIA on ..." or "to MERCHANT on ..."
        m = re.search(r"(?i)\bto\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
        if m:
            return _clean_merchant(m.group(1))
    else:
        # "via UPI from RAVI SHARMA on ..." or "from MERCHANT on ..."
        m = re.search(r"(?i)\bfrom\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
        if m:
            return _clean_merchant(m.group(1))
    # Fallback: look for text after 'to' / 'from' before 'on'
    m = re.search(r"(?i)\b(?:to|from)\s+([A-Z][A-Z0-9\s&.\-]{2,40}?)\s+on\s+\d", message)
    if m:
        return _clean_merchant(m.group(1))
    return "Unknown"


def _extract_merchant_card(message: str) -> str:
    m = re.search(r"(?i)\bat\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
    if m:
        return _clean_merchant(m.group(1))
    return "Unknown"


def _extract_merchant_imps_neft(message: str) -> str:
    m = re.search(r"(?i)\bfrom\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
    if m:
        return _clean_merchant(m.group(1))
    return "Unknown"


def _extract_merchant_atm(message: str) -> str:
    m = re.search(r"(?i)\bat\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
    if m:
        return _clean_merchant(m.group(1))
    return "ATM Withdrawal"


def _extract_merchant_transfer(message: str) -> str:
    m = re.search(r"(?i)\bto\s+([A-Z][A-Z0-9\s&.\-]+?)\s+on\s+\d", message)
    if m:
        return _clean_merchant(m.group(1))
    return "Unknown"


def _parse_upi(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "upi" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_upi(message, trans_type)
        reference = _extract_reference(message)
        gateway = _detect_gateway(message)
        desc = f"UPI {trans_type} to/from {merchant}"
        confidence = 0.92 if reference else 0.8
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="upi",
            payment_gateway=gateway,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


def _parse_card(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "card" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_card(message)
        reference = _extract_reference(message)
        desc = f"Card {trans_type} at {merchant}"
        confidence = 0.88 if reference else 0.75
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="card",
            payment_gateway=None,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


def _parse_imps(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "imps" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_imps_neft(message)
        reference = _extract_reference(message)
        desc = f"IMPS {trans_type} from/to {merchant}"
        confidence = 0.9 if reference else 0.78
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="imps",
            payment_gateway=None,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


def _parse_neft(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "neft" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_imps_neft(message)
        reference = _extract_reference(message)
        desc = f"NEFT {trans_type} from/to {merchant}"
        confidence = 0.9 if reference else 0.78
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="neft",
            payment_gateway=None,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


def _parse_atm(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "atm" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_atm(message)
        reference = _extract_reference(message)
        desc = f"ATM {trans_type} at {merchant}"
        confidence = 0.85
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="atm",
            payment_gateway=None,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


def _parse_transfer(message: str, trans_type: str) -> Optional[ParsedTransaction]:
    if "transfer" not in message.lower():
        return None
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        merchant = _extract_merchant_transfer(message)
        reference = _extract_reference(message)
        desc = f"Bank transfer {trans_type} to/from {merchant}"
        confidence = 0.82
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw=merchant,
            transaction_date=txn_date,
            payment_method="net_banking",
            payment_gateway=None,
            source_reference=reference,
            confidence=confidence,
            description=desc,
        )
    except SmsParseError:
        return None


# Matchers are tried in this order — more specific patterns first.
_MATCHERS = (
    _parse_upi,
    _parse_imps,
    _parse_neft,
    _parse_card,
    _parse_atm,
    _parse_transfer,
)


def parse_sms(message: str) -> ParsedTransaction:
    """Parse an SMS message into a ParsedTransaction.

    Tries each payment-method matcher in turn. Raises SmsParseError if no
    matcher can confidently extract a transaction.
    """
    if not message or not message.strip():
        raise SmsParseError("Empty message")

    trans_type = _detect_type(message)

    for matcher in _MATCHERS:
        result = matcher(message, trans_type)
        if result is not None:
            return result

    # Last-resort generic attempt: any amount + date in the message
    try:
        amount_paise = _extract_amount(message)
        txn_date = _extract_date(message)
        return ParsedTransaction(
            amount_paise=amount_paise,
            transaction_type=trans_type,
            merchant_raw="Unknown",
            transaction_date=txn_date,
            payment_method=_detect_payment_method(message),
            payment_gateway=_detect_gateway(message),
            source_reference=_extract_reference(message),
            confidence=0.5,
            description=f"Generic {trans_type} transaction",
        )
    except SmsParseError:
        raise SmsParseError("Unable to parse SMS as a transaction")
