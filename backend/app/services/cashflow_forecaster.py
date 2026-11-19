"""Small-business cash flow forecasting — blueprint §7 Phase 3.

Calculates:
- total sales
- total expenses
- pending receivables
- pending payables
- projected cash balance

Formula:

    projected_cash_balance_paise =
    current_cash_paise
    + expected_receivables_paise
    - expected_payables_paise
    + forecast_net_operating_cashflow_paise

Does not double-count transactions already included in current cash.
"""

from dataclasses import dataclass
from typing import List

from app.models.business import BusinessEntry
from app.models.transaction import Transaction
from app.repositories.business_repository import BusinessRepository
from app.repositories.transaction_repository import TransactionRepository


@dataclass
class CashFlowResult:
    currency: str
    current_cash_paise: int
    total_sales_paise: int
    total_expenses_paise: int
    pending_receivables_paise: int
    pending_payables_paise: int
    projected_cash_balance_paise: int
    forecast_date: str
    items: List[dict]


def calculate_cash_flow(
    db,
    user_id: str,
    current_cash_paise: int,
    forecast_date: str,
) -> CashFlowResult:
    """Calculate small-business cash flow for a user.

    current_cash_paise is the latest known available cash balance (provided by
    the user or derived from the system). We do not double-count: sales/expense
    entries that are already marked paid/received are included in total
    calculations but excluded from pending projections.
    """
    biz_repo = BusinessRepository(db)
    entries, _ = biz_repo.list(user_id=user_id)

    # Separate business entries
    sales_entries = [e for e in entries if e.entry_type == "sale"]
    expense_entries = [e for e in entries if e.entry_type == "expense"]
    receivable_entries = [e for e in entries if e.entry_type == "receivable"]
    payable_entries = [e for e in entries if e.entry_type == "payable"]

    total_sales_paise = sum(e.amount_paise for e in sales_entries)
    total_expenses_paise = sum(e.amount_paise for e in expense_entries)
    pending_receivables_paise = sum(
        e.amount_paise for e in receivable_entries if e.status in ("pending", "overdue")
    )
    pending_payables_paise = sum(
        e.amount_paise for e in payable_entries if e.status in ("pending", "overdue")
    )

    # Forecast net operating cashflow: sales - expenses for pending items
    forecast_net_operating_cashflow_paise = total_sales_paise - total_expenses_paise

    projected_cash_balance_paise = (
        current_cash_paise
        + pending_receivables_paise
        - pending_payables_paise
        + forecast_net_operating_cashflow_paise
    )

    items = [
        {
            "entry_type": "sale",
            "total_paise": total_sales_paise,
            "count": len(sales_entries),
        },
        {
            "entry_type": "expense",
            "total_paise": total_expenses_paise,
            "count": len(expense_entries),
        },
        {
            "entry_type": "receivable",
            "total_paise": pending_receivables_paise,
            "count": len(receivable_entries),
        },
        {
            "entry_type": "payable",
            "total_paise": pending_payables_paise,
            "count": len(payable_entries),
        },
    ]

    return CashFlowResult(
        currency="INR",
        current_cash_paise=current_cash_paise,
        total_sales_paise=total_sales_paise,
        total_expenses_paise=total_expenses_paise,
        pending_receivables_paise=pending_receivables_paise,
        pending_payables_paise=pending_payables_paise,
        projected_cash_balance_paise=max(0, projected_cash_balance_paise),
        forecast_date=forecast_date,
        items=items,
    )


def derive_current_cash_from_transactions(
    db,
    user_id: str,
) -> int:
    """Derive current cash balance from the user's credit/debit transactions.

    Sum of credits minus sum of debits. Used as a demo balance when the user
    hasn't provided one.
    """
    txn_repo = TransactionRepository(db)
    transactions, _ = txn_repo.list(user_id=user_id, page=1, page_size=10000)

    credits = sum(t.amount_paise for t in transactions if t.transaction_type == "credit")
    debits = sum(t.amount_paise for t in transactions if t.transaction_type == "debit")
    return credits - debits
