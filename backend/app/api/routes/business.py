"""Small-business cash flow API routes — CONTRACT.md §12."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import DbSession, get_current_user
from app.models.business import BusinessEntry
from app.models.user import User
from app.repositories.business_repository import BusinessRepository
from app.schemas.business import (
    BusinessEntryCreate,
    BusinessEntryItem,
    CashFlowItem,
    CashFlowRequest,
    CashFlowResponse,
    InvoiceItem,
    InvoiceRequest,
    InvoiceResponse,
)
from app.services.cashflow_forecaster import calculate_cash_flow, derive_current_cash_from_transactions

router = APIRouter()


def _entry_to_item(entry: BusinessEntry) -> BusinessEntryItem:
    return BusinessEntryItem(
        id=entry.id,
        entry_type=entry.entry_type,
        description=entry.description,
        amount_paise=entry.amount_paise,
        due_date=entry.due_date.isoformat() if entry.due_date else None,
        status=entry.status,
        counterparty=entry.counterparty,
    )


@router.get(
    "/business/cashflow",
    response_model=CashFlowResponse,
    tags=["business"],
    summary="Get small-business cash flow",
)
def get_cashflow(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    current_cash_paise: int = 0,
    forecast_date: str | None = None,
):
    """Calculate projected cash balance for the user's business entries."""
    from app.utils.dates import now_utc, IST_TZ
    from datetime import datetime

    if forecast_date is None:
        forecast_date = now_utc().astimezone(IST_TZ).date().isoformat()

    result = calculate_cash_flow(
        db=db,
        user_id=current_user.id,
        current_cash_paise=current_cash_paise,
        forecast_date=forecast_date,
    )
    return CashFlowResponse(
        currency=result.currency,
        current_cash_paise=result.current_cash_paise,
        total_sales_paise=result.total_sales_paise,
        total_expenses_paise=result.total_expenses_paise,
        pending_receivables_paise=result.pending_receivables_paise,
        pending_payables_paise=result.pending_payables_paise,
        projected_cash_balance_paise=result.projected_cash_balance_paise,
        forecast_date=result.forecast_date,
        items=[CashFlowItem(**i) for i in result.items],
    )


@router.post(
    "/business/entries",
    response_model=BusinessEntryItem,
    status_code=status.HTTP_201_CREATED,
    tags=["business"],
    summary="Create a business entry",
)
def create_business_entry(
    payload: BusinessEntryCreate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    """Create a business entry (sale/expense/receivable/payable)."""
    repo = BusinessRepository(db)
    due_date = None
    if payload.due_date:
        from app.utils.dates import parse_date_iso
        try:
            due_date = parse_date_iso(payload.due_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="due_date must be YYYY-MM-DD",
            )
    entry = repo.create(
        user_id=current_user.id,
        entry_type=payload.entry_type,
        description=payload.description.strip(),
        amount_paise=payload.amount_paise,
        due_date=due_date,
        status="pending",
        counterparty=payload.counterparty,
    )
    return _entry_to_item(entry)


@router.post(
    "/business/invoices",
    response_model=InvoiceResponse,
    tags=["business"],
    summary="Generate an illustrative GST invoice",
)
def generate_invoice(
    payload: InvoiceRequest,
):
    """Generate an illustrative GST invoice (not a compliant GST filing system)."""
    subtotal = sum(item.quantity * item.unit_price_paise for item in payload.items)

    # Simple GST split: for intra-state (same place of supply as default), split CGST/SGST.
    # For MVP, treat all as illustrative; place_of_supply is recorded but not validated
    # against a GST jurisdiction master.
    cgst = int(subtotal * 900 / 10000)  # 9% CGST illustrative
    sgst = int(subtotal * 900 / 10000)  # 9% SGST illustrative
    igst = 0
    total = subtotal + cgst + sgst + igst

    return InvoiceResponse(
        invoice_number=payload.invoice_number,
        subtotal_paise=subtotal,
        cgst_paise=cgst,
        sgst_paise=sgst,
        igst_paise=igst,
        total_paise=total,
        tax_calculation_status="illustrative",
    )
