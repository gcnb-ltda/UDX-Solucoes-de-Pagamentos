import uuid
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.dependencies import require_roles
from app.models import AuditLog, Branch, LedgerAccount, LedgerEntry, PaymentAccount, Transaction, User, UserRole
from app.schemas import AuditLogOut, PaymentAccountCreate, PaymentAccountOut, TransactionOut, TrialBalanceLine
from app.security_controls import audit_event
from app.services.ledger import assert_transaction_balanced, post_pix_outgoing

router = APIRouter(prefix="/backoffice", tags=["backoffice"])


class CompleteTransactionRequest(BaseModel):
    external_id: str | None = Field(default=None, max_length=120)


@router.get("/accounts", response_model=list[PaymentAccountOut])
def list_payment_accounts(actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.finance, UserRole.accounting)), db: Session = Depends(get_db)) -> list[PaymentAccount]:
    return list(db.scalars(select(PaymentAccount).where(PaymentAccount.company_id == actor.company_id).order_by(PaymentAccount.created_at)))


@router.post("/accounts", response_model=PaymentAccountOut, status_code=status.HTTP_201_CREATED)
def create_payment_account(payload: PaymentAccountCreate, request: Request, actor: User = Depends(require_roles(UserRole.admin, UserRole.finance)), db: Session = Depends(get_db)) -> PaymentAccount:
    if payload.branch_id:
        branch = db.scalar(select(Branch).where(Branch.id == payload.branch_id, Branch.company_id == actor.company_id, Branch.is_active.is_(True)))
        if not branch:
            raise HTTPException(status_code=400, detail="Invalid branch")
    account = PaymentAccount(company_id=actor.company_id, branch_id=payload.branch_id, name=payload.name, currency="BRL", status="active")
    db.add(account)
    db.flush()
    audit_event(db, request, action="finance.account.created", actor=actor, target_type="payment_account", target_id=account.id)
    db.commit()
    db.refresh(account)
    return account


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(transaction_status: str | None = None, kind: str | None = None, limit: int = 100, actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.finance, UserRole.accounting)), db: Session = Depends(get_db)) -> list[Transaction]:
    limit = min(max(limit, 1), 200)
    query = select(Transaction).where(Transaction.company_id == actor.company_id)
    if transaction_status:
        query = query.where(Transaction.status == transaction_status)
    if kind:
        query = query.where(Transaction.kind == kind)
    return list(db.scalars(query.order_by(Transaction.created_at.desc()).limit(limit)))


@router.post("/transactions/{transaction_id}/complete", response_model=TransactionOut)
def complete_transaction(transaction_id: uuid.UUID, payload: CompleteTransactionRequest, request: Request, actor: User = Depends(require_roles(UserRole.admin, UserRole.finance)), db: Session = Depends(get_db)) -> Transaction:
    transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.company_id == actor.company_id).with_for_update())
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not settings.allow_manual_settlement:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Manual settlement is disabled")
    if transaction.kind != "pix_outgoing":
        raise HTTPException(status_code=400, detail="Only Pix transfers can be completed")
    if transaction.status != "pending":
        raise HTTPException(status_code=409, detail="Transaction is not pending")
    try:
        post_pix_outgoing(db, transaction)
        assert_transaction_balanced(db, transaction.id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    transaction.external_id = payload.external_id
    audit_event(db, request, action="finance.pix.completed_manual", actor=actor, target_type="transaction", target_id=transaction.id, details={"external_id": payload.external_id})
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/ledger/trial-balance", response_model=list[TrialBalanceLine])
def trial_balance(actor: User = Depends(require_roles(UserRole.admin, UserRole.finance, UserRole.accounting)), db: Session = Depends(get_db)) -> list[TrialBalanceLine]:
    accounts = list(db.scalars(select(LedgerAccount).where(LedgerAccount.company_id == actor.company_id).order_by(LedgerAccount.code)))
    entries = list(db.scalars(select(LedgerEntry).where(LedgerEntry.company_id == actor.company_id)))
    totals: dict[uuid.UUID, dict[str, Decimal]] = defaultdict(lambda: {"debit": Decimal("0"), "credit": Decimal("0")})
    for entry in entries:
        totals[entry.ledger_account_id][entry.side] += Decimal(entry.amount)
    return [TrialBalanceLine(ledger_account_id=account.id, code=account.code, name=account.name, account_type=account.account_type, debit=totals[account.id]["debit"], credit=totals[account.id]["credit"], net=totals[account.id]["debit"] - totals[account.id]["credit"]) for account in accounts]


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(limit: int = 100, actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.accounting)), db: Session = Depends(get_db)) -> list[AuditLog]:
    limit = min(max(limit, 1), 200)
    return list(db.scalars(select(AuditLog).where(AuditLog.company_id == actor.company_id).order_by(AuditLog.created_at.desc()).limit(limit)))
