"""CSV and PDF statement parsing.

CSV: configurable column mapping with common statement headings, row-level
validation, returns accepted/rejected counts with per-row errors.

PDF: text extraction via pdfplumber. Parses only supported statement formats.
If extraction fails, raises UnsupportedFormatError — never pretends OCR.
"""

import csv
import io
import re
from dataclasses import dataclass
from typing import List, Optional

from app.utils.dates import parse_indian_date
from app.utils.money import to_paise


class UnsupportedFormatError(Exception):
    """Raised when a PDF cannot be parsed (no OCR fallback)."""


@dataclass
class ParsedRow:
    amount_paise: int
    transaction_type: str
    merchant: str
    category: Optional[str]
    payment_method: str
    transaction_date: str  # YYYY-MM-DD
    source_reference: Optional[str]
    description: Optional[str]


# Common statement column headings -> canonical field names
COLUMN_ALIASES = {
    "amount": {"amount", "amt", "transaction amount", "amount (inr)", "value"},
    "type": {"type", "transaction type", "txn type", "dr/cr", "credit/debit"},
    "merchant": {"merchant", "payee", "counterparty", "description", "narration", "remarks"},
    "category": {"category", "txn category"},
    "payment_method": {"payment method", "mode", "payment mode", "method"},
    "date": {"date", "transaction date", "txn date", "value date", "posting date"},
    "reference": {"reference", "ref", "ref no", "transaction ref", "upi ref", "utr"},
}


def _normalize_heading(heading: str) -> str:
    return heading.strip().lower()


def _map_columns(headings: List[str]) -> dict:
    """Map raw CSV headings to canonical field names. Returns {canonical: index}."""
    mapping = {}
    normalized = [_normalize_heading(h) for h in headings]
    for canonical, aliases in COLUMN_ALIASES.items():
        for idx, nh in enumerate(normalized):
            if nh in aliases:
                mapping[canonical] = idx
                break
    return mapping


def _detect_type(value: str) -> str:
    low = value.strip().lower()
    if low in ("credit", "cr", "+"):
        return "credit"
    if low in ("debit", "dr", "-"):
        return "debit"
    return "debit"


def _detect_payment_method(value: str) -> str:
    low = value.strip().lower()
    if "upi" in low:
        return "upi"
    if "card" in low:
        return "card"
    if "imps" in low:
        return "imps"
    if "neft" in low:
        return "neft"
    if "atm" in low:
        return "atm"
    if "transfer" in low or "net" in low:
        return "net_banking"
    return "other"


def _clean_merchant(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"\s+", " ", raw)
    return raw or "Unknown"


def parse_csv(file_content: bytes, filename: str = "upload.csv") -> dict:
    """Parse a CSV statement.

    Returns:
        {"rows": [ParsedRow, ...], "errors": [{"row": int, "code": str, "message": str}]}
    """
    text = file_content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"rows": [], "errors": [{"row": 0, "code": "EMPTY_FILE", "message": "CSV file is empty"}]}

    headings = rows[0]
    col_map = _map_columns(headings)

    required = ("amount", "date", "merchant")
    missing = [r for r in required if r not in col_map]
    if missing:
        return {
            "rows": [],
            "errors": [{"row": 0, "code": "MISSING_COLUMNS", "message": f"Missing columns: {', '.join(missing)}"}],
        }

    parsed_rows: List[ParsedRow] = []
    errors: List[dict] = []

    for i, row in enumerate(rows[1:], start=2):  # row 1 = header
        if not row or all(cell.strip() == "" for cell in row):
            continue  # skip blank rows
        try:
            amount_raw = row[col_map["amount"]].strip()
            amount_paise = to_paise(amount_raw)

            date_raw = row[col_map["date"]].strip()
            txn_date = parse_indian_date(date_raw)

            merchant_idx = col_map.get("merchant")
            merchant = (
                row[merchant_idx].strip()
                if merchant_idx is not None and merchant_idx < len(row)
                else "Unknown"
            )

            txn_type_idx = col_map.get("type")
            txn_type = (
                _detect_type(row[txn_type_idx])
                if txn_type_idx is not None and txn_type_idx < len(row)
                else "debit"
            )

            category_idx = col_map.get("category")
            category = (
                row[category_idx].strip()
                if category_idx is not None and category_idx < len(row)
                else None
            )

            pm_idx = col_map.get("payment_method")
            payment_method = (
                _detect_payment_method(row[pm_idx])
                if pm_idx is not None and pm_idx < len(row)
                else "other"
            )

            ref_idx = col_map.get("reference")
            source_reference = (
                row[ref_idx].strip()
                if ref_idx is not None and ref_idx < len(row)
                else None
            )

            parsed_rows.append(ParsedRow(
                amount_paise=amount_paise,
                transaction_type=txn_type,
                merchant=merchant,
                category=category,
                payment_method=payment_method,
                transaction_date=txn_date.isoformat(),
                source_reference=source_reference,
                description=None,
            ))
        except Exception as exc:  # noqa: BLE001 - row-level validation, capture all
            errors.append({
                "row": i,
                "code": "INVALID_ROW",
                "message": str(exc) or "Row could not be parsed",
            })

    return {"rows": parsed_rows, "errors": errors}


def parse_pdf(file_content: bytes, filename: str = "upload.pdf") -> dict:
    """Extract text from a PDF statement using pdfplumber.

    Only text-based (digitally generated) PDFs are supported. Scanned/image
    PDFs without an embedded text layer raise UnsupportedFormatError — we do
    not pretend OCR is implemented.
    """
    try:
        import pdfplumber  # noqa: F401  (imported here to keep it optional)
    except ImportError:
        raise UnsupportedFormatError("pdfplumber is not installed")

    import pdfplumber as _pdfplumber

    extracted_texts: List[str] = []
    try:
        pdf_io = io.BytesIO(file_content)
        with _pdfplumber.open(pdf_io) as pdf:
            if len(pdf.pages) == 0:
                return {"text": "", "pages": 0, "errors": []}
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_texts.append(text)
    except Exception as exc:  # noqa: BLE001
        raise UnsupportedFormatError(f"PDF extraction failed: {exc}")

    if not extracted_texts:
        raise UnsupportedFormatError(
            "No text found in PDF — scanned/image PDFs are not supported (no OCR)"
        )

    return {
        "text": "\n".join(extracted_texts),
        "pages": len(extracted_texts),
        "errors": [],
    }


def parse_pdf_rows(file_content: bytes, filename: str = "upload.pdf") -> dict:
    """Parse a PDF statement into rows.

    Extracts text and attempts line-by-line parsing for simple statement
    layouts that contain an amount and a date on the same line. Complex
    layouts return zero parsed rows with the raw text available separately.
    """
    result = parse_pdf(file_content, filename)
    lines = result["text"].splitlines()

    amount_re = re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+\.?\d*)", re.IGNORECASE)
    date_re = re.compile(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})")

    rows: List[dict] = []
    errors: List[dict] = []

    for i, line in enumerate(lines, start=1):
        amt_m = amount_re.search(line)
        date_m = date_re.search(line)
        if amt_m and date_m:
            try:
                amount_paise = to_paise(amt_m.group(1))
                txn_date = parse_indian_date(date_m.group(1))
                # Determine type/merchant heuristically from the line
                txn_type = "credit" if any(k in line.lower() for k in ("credit", "cr", "deposit")) else "debit"
                payment_method = "other"
                for kw, method in (
                    ("upi", "upi"), ("card", "card"), ("imps", "imps"),
                    ("neft", "neft"), ("atm", "atm"), ("transfer", "net_banking"),
                ):
                    if kw in line.lower():
                        payment_method = method
                        break
                after_date = line.split(date_m.group(1), 1)[-1].strip()
                merchant = _clean_merchant(after_date) or "Unknown"
                rows.append({
                    "amount_paise": amount_paise,
                    "transaction_type": txn_type,
                    "merchant": merchant,
                    "category": None,
                    "payment_method": payment_method,
                    "transaction_date": txn_date.isoformat(),
                    "source_reference": None,
                    "description": line.strip(),
                })
            except Exception as exc:  # noqa: BLE001
                errors.append({"row": i, "code": "INVALID_ROW", "message": str(exc)})

    return {"rows": rows, "errors": errors}
