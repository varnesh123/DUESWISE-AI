"""Transaction ingestion API routes — CONTRACT.md §6.

Endpoints:
- POST /api/v1/transactions/ingest/sms
- POST /api/v1/transactions/ingest/file  (multipart CSV/PDF)
- POST /api/v1/transactions/ingest/aa-mock

Business logic lives in services/repositories; routes are thin.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies import DbSession, get_current_user
from app.models.user import User
from app.schemas.common import ErrorDetail, ErrorResponse
from app.schemas.ingestion import (
    AAMockRequest,
    AAMockResponse,
    FileIngestResponse,
    SmsIngestRequest,
    SmsIngestResponse,
    UnifiedIngestRequest,
    UnifiedIngestResponse,
)
from app.schemas.transaction import TransactionItem
from app.services.ai_client import AIClient
from app.services.categorisation import categorise_merchant
from app.services.manual_transaction import create_manual_transaction
from app.services.statement_parser import (
    UnsupportedFormatError,
    parse_csv,
    parse_pdf_rows,
)
from app.services.transaction_parser import SmsParseError, ParsedTransaction, parse_sms
from app.repositories.ingestion_repository import IngestionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.utils.dates import IST_TZ, now_utc, parse_date_iso
from app.utils.money import validate_amount_paise
from app.models.transaction import Transaction
from app.config import settings

router = APIRouter()

ai_client = AIClient()

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024

_SUPPORTED_CSV_TYPES = {"text/csv", "application/csv", "text/plain"}
_SUPPORTED_PDF_TYPES = {"application/pdf"}


def _txn_to_item(txn: Transaction) -> TransactionItem:
    return TransactionItem(
        id=txn.id,
        amount_paise=txn.amount_paise,
        currency=txn.currency,
        transaction_type=txn.transaction_type,
        merchant_raw=txn.merchant_raw,
        merchant_normalized=txn.merchant_normalized,
        category=txn.category,
        payment_method=txn.payment_method,
        payment_gateway=txn.payment_gateway,
        transaction_date=txn.transaction_date.isoformat(),
        source=txn.source,
        source_reference=txn.source_reference,
        confidence=txn.confidence,
        description=txn.description,
        is_suspicious=txn.is_suspicious,
    )


def _ingest_parsed_transaction(
    db: DbSession,
    repo: TransactionRepository,
    ing_repo: IngestionRepository,
    record,
    user_id: str,
    parsed: ParsedTransaction,
    source: str,
    filename: Optional[str] = None,
) -> dict:
    """Run one parsed transaction through categorisation + dedup + insert.

    Returns a dict with keys: imported (bool), duplicate (bool), warning (str|None).
    """
    # Categorise — try AI first for unresolved merchants, then deterministic.
    ai_result = ai_client.merchant_normalize(parsed.merchant_raw, "INR")
    normalized, category, confidence = categorise_merchant(
        parsed.merchant_raw,
        ai_normalized=ai_result.get("merchant_normalized") if ai_result else None,
        ai_category=ai_result.get("category") if ai_result else None,
        ai_confidence=ai_result.get("confidence") if ai_result else None,
    )

    # Duplicate check
    existing = repo.find_duplicate(
        user_id=user_id,
        amount_paise=parsed.amount_paise,
        transaction_date=parsed.transaction_date,
        transaction_type=parsed.transaction_type,
        merchant_normalized=normalized,
        payment_method=parsed.payment_method,
        source=source,
        source_reference=parsed.source_reference,
    )
    if existing:
        return {
            "imported": False,
            "duplicate": True,
            "warning": "Duplicate transaction skipped",
            "transaction": _txn_to_item(existing),
        }

    txn = repo.create(
        user_id=user_id,
        amount_paise=parsed.amount_paise,
        currency="INR",
        transaction_type=parsed.transaction_type,
        merchant_raw=parsed.merchant_raw,
        merchant_normalized=normalized,
        category=category,
        payment_method=parsed.payment_method,
        payment_gateway=parsed.payment_gateway,
        transaction_date=parsed.transaction_date,
        source=source,
        source_reference=parsed.source_reference,
        confidence=parsed.confidence if parsed.confidence > confidence else confidence,
        description=parsed.description,
        is_suspicious=False,
    )
    return {"imported": True, "duplicate": False, "warning": None, "transaction": _txn_to_item(txn)}


@router.post(
    "/transactions/ingest",
    response_model=UnifiedIngestResponse,
    tags=["ingestion"],
    summary="Ingest a transaction (manual entry or SMS text)",
)
def ingest_transaction(
    payload: UnifiedIngestRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Ingest a transaction through the contract path.

    Two supported shapes:
    - manual: ``merchant_raw`` + ``amount_paise`` (+ optional date/type/category)
    - sms: ``message`` containing a bank/UPI transaction message

    Manual entries are categorised deterministically (AI-assisted only when
    enabled), deduplicated, and stored exactly like ``/transactions/manual``.
    """
    merchant = (payload.merchant_raw or payload.merchant or "").strip()

    # ---- SMS text path ------------------------------------------------
    if payload.message and not merchant:
        try:
            parsed = parse_sms(payload.message)
        except SmsParseError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parsing failed: {exc}",
            )
        repo = TransactionRepository(db)
        ing_repo = IngestionRepository(db)
        record = ing_repo.create(user_id=current_user.id, source="sms")
        result = _ingest_parsed_transaction(
            db, repo, ing_repo, record, current_user.id, parsed, "sms"
        )
        imported = 1 if result["imported"] else 0
        ing_repo.update(
            record,
            status="completed",
            imported_count=imported,
            rejected_count=0 if imported else 1,
            duplicates_skipped=1 if result["duplicate"] else 0,
        )
        return UnifiedIngestResponse(
            status="completed",
            transaction=result.get("transaction"),
            duplicate=result["duplicate"],
            warnings=[result["warning"]] if result.get("warning") else [],
            processing={"source": "sms"},
        )

    # ---- Manual entry path --------------------------------------------
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="merchant_raw is required when message is not provided",
        )
    if payload.amount_paise is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="amount_paise is required",
        )
    try:
        validate_amount_paise(payload.amount_paise)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if payload.transaction_type not in ("credit", "debit"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="transaction_type must be credit or debit",
        )

    if payload.transaction_date:
        try:
            txn_date = parse_date_iso(payload.transaction_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="transaction_date must be YYYY-MM-DD",
            )
    else:
        txn_date = now_utc().astimezone(IST_TZ).date()

    ai_result = ai_client.merchant_normalize(merchant, "INR")
    normalized, category, confidence = categorise_merchant(
        merchant,
        ai_normalized=ai_result.get("merchant_normalized") if ai_result else None,
        ai_category=ai_result.get("category") if ai_result else None,
        ai_confidence=ai_result.get("confidence") if ai_result else None,
    )
    if payload.category:
        category = payload.category

    ing_repo = IngestionRepository(db)
    record = ing_repo.create(user_id=current_user.id, source="manual")

    result = create_manual_transaction(
        db,
        user_id=current_user.id,
        amount_paise=payload.amount_paise,
        transaction_type=payload.transaction_type,
        merchant_raw=merchant,
        merchant_normalized=normalized,
        category=category,
        payment_method=payload.payment_method,
        transaction_date=txn_date,
    )

    if result.duplicate:
        ing_repo.update(
            record, status="completed", imported_count=0,
            rejected_count=0, duplicates_skipped=1,
        )
        return UnifiedIngestResponse(
            status="duplicate",
            transaction=_txn_to_item(result.transaction),
            duplicate=True,
            warnings=["Duplicate transaction skipped"],
            processing={"source": "manual"},
        )

    ing_repo.update(record, status="completed", imported_count=1, rejected_count=0)

    return UnifiedIngestResponse(
        status="completed",
        transaction=_txn_to_item(result.transaction),
        duplicate=False,
        processing={
            "source": "manual",
            "ai_used": bool(ai_result),
            "categorisation_confidence": confidence,
        },
    )


@router.post(
    "/transactions/ingest/sms",
    response_model=SmsIngestResponse,
    tags=["ingestion"],
    summary="Ingest a single SMS",
)
def ingest_sms(
    payload: SmsIngestRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Parse one SMS message and ingest it as a transaction.

    Returns a documented parsing error (422) for unrecognised messages —
    never a fabricated transaction.
    """
    repo = TransactionRepository(db)
    ing_repo = IngestionRepository(db)
    record = ing_repo.create(user_id=current_user.id, source="sms")

    try:
        parsed = parse_sms(payload.message)
    except SmsParseError as exc:
        ing_repo.update(
            record, status="failed", imported_count=0, rejected_count=1,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parsing failed: {exc}",
        )

    result = _ingest_parsed_transaction(
        db, repo, ing_repo, record, current_user.id, parsed, "sms"
    )

    imported = 1 if result["imported"] else 0
    rejected = 0 if result["imported"] else 1
    ing_repo.update(
        record,
        status="completed",
        imported_count=imported,
        rejected_count=rejected,
        duplicates_skipped=1 if result["duplicate"] else 0,
    )

    return SmsIngestResponse(
        status="completed",
        transaction=result.get("transaction"),
        duplicate=result["duplicate"],
        warnings=[result["warning"]] if result.get("warning") else [],
    )


@router.post(
    "/transactions/ingest/file",
    response_model=FileIngestResponse,
    tags=["ingestion"],
    summary="Ingest a CSV or PDF statement file",
)
def ingest_file(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    source: str = Form("csv"),
):
    """Ingest an uploaded CSV or PDF statement.

    Validates file type and size. Parses each row, categorises, deduplicates,
    and inserts. Returns accepted/rejected counts with per-row errors.
    """
    if source not in ("csv", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="source must be 'csv' or 'pdf'",
        )

    content_type = (file.content_type or "").lower()
    if source == "csv" and content_type not in _SUPPORTED_CSV_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type — expected CSV",
        )
    if source == "pdf" and content_type not in _SUPPORTED_PDF_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type — expected PDF",
        )

    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    repo = TransactionRepository(db)
    ing_repo = IngestionRepository(db)
    record = ing_repo.create(
        user_id=current_user.id, source=source, filename=file.filename
    )

    try:
        if source == "csv":
            parsed = parse_csv(file_content, file.filename or "upload.csv")
        else:
            parsed = parse_pdf_rows(file_content, file.filename or "upload.pdf")
    except UnsupportedFormatError as exc:
        ing_repo.update(
            record, status="failed", imported_count=0, rejected_count=0,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        )
    except Exception as exc:  # noqa: BLE001
        ing_repo.update(
            record, status="failed", imported_count=0, rejected_count=0,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parsing failed: {exc}",
        )

    rows: List[dict] = parsed["rows"]
    row_errors: List[dict] = parsed["errors"]

    imported_count = 0
    rejected_count = len(row_errors)
    duplicates_skipped = 0
    transaction_items: List[TransactionItem] = []

    for row in rows:
        try:
            from app.services.transaction_parser import ParsedTransaction
            from app.utils.dates import parse_date_iso
            parsed_txn = ParsedTransaction(
                amount_paise=row.amount_paise,
                transaction_type=row.transaction_type,
                merchant_raw=row.merchant,
                transaction_date=parse_date_iso(row.transaction_date),
                payment_method=row.payment_method,
                payment_gateway=None,
                source_reference=row.source_reference,
                confidence=0.9,
                description=row.description,
            )
            result = _ingest_parsed_transaction(
                db, repo, ing_repo, record, current_user.id, parsed_txn, source,
                filename=file.filename,
            )
            if result["imported"]:
                imported_count += 1
                transaction_items.append(result["transaction"])
            elif result["duplicate"]:
                duplicates_skipped += 1
            else:
                rejected_count += 1
        except Exception as exc:  # noqa: BLE001
            rejected_count += 1
            row_errors.append({
                "row": None,
                "code": "INVALID_ROW",
                "message": str(exc),
            })

    ing_repo.update(
        record,
        status="completed",
        imported_count=imported_count,
        rejected_count=rejected_count,
        duplicates_skipped=duplicates_skipped,
    )

    return FileIngestResponse(
        ingestion_id=record.id,
        status="completed",
        imported_count=imported_count,
        rejected_count=rejected_count,
        duplicates_skipped=duplicates_skipped,
        errors=row_errors,
    )


@router.post(
    "/transactions/ingest/aa-mock",
    response_model=AAMockResponse,
    tags=["ingestion"],
    summary="Ingest mock Account Aggregator data",
)
def ingest_aa_mock(
    payload: AAMockRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Synthetic AA-style ingestion.

    Demonstrates the consent → FIU-FIP → normalisation → pipeline boundary.
    Uses synthetic mock data only — never connects to real banking systems.
    """
    # Record consent state (demo: consent_id is stored but not validated
    # against a real AA ecosystem, which does not exist in the MVP).
    repo = TransactionRepository(db)
    ing_repo = IngestionRepository(db)
    record = ing_repo.create(
        user_id=current_user.id, source="aa_mock",
        filename=f"aa_mock_{payload.account_reference}.json",
    )

    # Synthetic mock AA payload — deterministic, no real bank data.
    mock_transactions = [
        {
            "amount_paise": 450000,
            "transaction_type": "credit",
            "merchant_raw": "SALARY CREDIT",
            "transaction_date": "2026-10-31",
            "payment_method": "net_banking",
            "source_reference": f"AA-REF-{payload.account_reference}-001",
            "description": "Monthly salary credit",
        },
        {
            "amount_paise": 2000000,
            "transaction_type": "debit",
            "merchant_raw": "HOME LOAN EMI",
            "transaction_date": "2026-11-05",
            "payment_method": "net_banking",
            "source_reference": f"AA-REF-{payload.account_reference}-002",
            "description": "Home loan EMI auto-debit",
        },
        {
            "amount_paise": 85000,
            "transaction_type": "debit",
            "merchant_raw": "GROCERY STORE",
            "transaction_date": "2026-11-10",
            "payment_method": "upi",
            "source_reference": f"AA-REF-{payload.account_reference}-003",
            "description": "UPI grocery purchase",
        },
    ]

    imported_count = 0
    duplicates_skipped = 0

    for m in mock_transactions:
        try:
            txn_date = parse_date_iso(m["transaction_date"])
        except ValueError:
            continue

        existing = repo.find_duplicate(
            user_id=current_user.id,
            amount_paise=m["amount_paise"],
            transaction_date=txn_date,
            transaction_type=m["transaction_type"],
            merchant_normalized=m["merchant_raw"],
            payment_method=m["payment_method"],
            source="aa_mock",
            source_reference=m["source_reference"],
        )
        if existing:
            duplicates_skipped += 1
            continue

        ai_result = ai_client.merchant_normalize(m["merchant_raw"], "INR")
        normalized, category, confidence = categorise_merchant(
            m["merchant_raw"],
            ai_normalized=ai_result.get("merchant_normalized") if ai_result else None,
            ai_category=ai_result.get("category") if ai_result else None,
            ai_confidence=ai_result.get("confidence") if ai_result else None,
        )

        repo.create(
            user_id=current_user.id,
            amount_paise=m["amount_paise"],
            currency="INR",
            transaction_type=m["transaction_type"],
            merchant_raw=m["merchant_raw"],
            merchant_normalized=normalized,
            category=category,
            payment_method=m["payment_method"],
            payment_gateway=None,
            transaction_date=txn_date,
            source="aa_mock",
            source_reference=m["source_reference"],
            confidence=confidence,
            description=m.get("description"),
            is_suspicious=False,
        )
        imported_count += 1

    ing_repo.update(
        record,
        status="completed",
        imported_count=imported_count,
        rejected_count=0,
        duplicates_skipped=duplicates_skipped,
    )

    return AAMockResponse(
        status="completed",
        source="aa_mock",
        imported_count=imported_count,
        duplicates_skipped=duplicates_skipped,
    )
