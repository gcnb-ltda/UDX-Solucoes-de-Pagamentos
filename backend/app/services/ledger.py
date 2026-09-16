import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import LedgerAccount, LedgerEntry, Transaction

SETTLEMENT_CASH_CODE = "1100"
CUSTOMER_FUNDS_CODE = "2100"


def _ensure_ledger_account(db: Session, *, company_id, code: str, name: str, account_type: str) -> LedgerAccount:
    stmt = insert(LedgerAccount).values(id=uuid.uuid4(), company_id=company_id, code=code, name=name, account_type=account_type, currency="BRL", is_active=True).on_conflict_do_nothing(constraint="uq_ledger_accounts_company_code")
    db.execute(stmt)
    account = db.scalar(select(LedgerAccount).where(LedgerAccount.company_id == company_id, LedgerAccount.code == code))
    if not account:
        raise RuntimeError("failed to provision ledger account")
    return account


def get_or_create_default_ledger_accounts(db: Session, company_id) -> tuple[LedgerAccount, LedgerAccount]:
    cash = _ensure_ledger_account(db, company_id=company_id, code=SETTLEMENT_CASH_CODE, name="Settlement Cash", account_type="asset")
    customer_funds = _ensure_ledger_account(db, company_id=company_id, code=CUSTOMER_FUNDS_CODE, name="Customer Funds", account_type="liability")
    return cash, customer_funds


def post_pix_outgoing(db: Session, transaction: Transaction) -> list[LedgerEntry]:
    existing = db.scalar(select(LedgerEntry.id).where(LedgerEntry.transaction_id == transaction.id))
    if existing:
        raise ValueError("transaction already posted")
    if transaction.status != "pending" or transaction.kind != "pix_outgoing":
        raise ValueError("transaction is not a pending outgoing pix")
    if Decimal(transaction.amount) <= 0:
        raise ValueError("transaction amount must be positive")
    cash, customer_funds = get_or_create_default_ledger_accounts(db, transaction.company_id)
    debit = LedgerEntry(company_id=transaction.company_id, transaction_id=transaction.id, ledger_account_id=customer_funds.id, side="debit", amount=transaction.amount, description="Pix outgoing - reduction of customer funds liability")
    credit = LedgerEntry(company_id=transaction.company_id, transaction_id=transaction.id, ledger_account_id=cash.id, side="credit", amount=transaction.amount, description="Pix outgoing - settlement cash")
    db.add_all([debit, credit])
    transaction.status = "completed"
    transaction.completed_at = datetime.now(UTC)
    db.flush()
    return [debit, credit]


def assert_transaction_balanced(db: Session, transaction_id) -> None:
    entries = list(db.scalars(select(LedgerEntry).where(LedgerEntry.transaction_id == transaction_id)))
    debit = sum((Decimal(entry.amount) for entry in entries if entry.side == "debit"), Decimal("0"))
    credit = sum((Decimal(entry.amount) for entry in entries if entry.side == "credit"), Decimal("0"))
    if debit != credit:
        raise ValueError("ledger transaction is not balanced")
