import hashlib
import json
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models import PaymentAccount, PixTransfer, Transaction, User, UserRole
from app.schemas import PixTransferCreate, PixTransferOut
from app.security import hash_sensitive_value
from app.security_controls import audit_event

router = APIRouter(prefix="/pix", tags=["pix"])


def _fingerprint(payload: PixTransferCreate) -> str:
    raw = json.dumps({"account_id": str(payload.account_id), "amount": str(payload.amount.quantize(Decimal("0.01"))), "pix_key_hash": hash_sensitive_value(payload.pix_key.strip()), "counterparty_name": payload.counterparty_name, "counterparty_tax_id": payload.counterparty_tax_id, "description": payload.description, "reference": payload.reference}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _response(transaction: Transaction, pix_transfer: PixTransfer) -> PixTransferOut:
    if transaction.account_id is None:
        raise RuntimeError("Pix transaction without payment account")
    return PixTransferOut(id=pix_transfer.id, transaction_id=transaction.id, account_id=transaction.account_id, amount=transaction.amount, currency=transaction.currency, status=transaction.status, pix_key_last4=pix_transfer.pix_key_last4, counterparty_name=pix_transfer.counterparty_name, reference=transaction.reference, created_at=transaction.created_at)


@router.post("/transfers", response_model=PixTransferOut, status_code=status.HTTP_201_CREATED)
def create_pix_transfer(payload: PixTransferCreate, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.finance)), db: Session = Depends(get_db)) -> PixTransferOut:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    if len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    account = db.scalar(select(PaymentAccount).where(PaymentAccount.id == payload.account_id, PaymentAccount.company_id == actor.company_id, PaymentAccount.status == "active"))
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")
    fingerprint = _fingerprint(payload)
    existing = db.scalar(select(Transaction).where(Transaction.company_id == actor.company_id, Transaction.idempotency_key == idempotency_key))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency-Key already used with different payload")
        pix_transfer = db.scalar(select(PixTransfer).where(PixTransfer.transaction_id == existing.id))
        if not pix_transfer:
            raise HTTPException(status_code=409, detail="Idempotency conflict")
        return _response(existing, pix_transfer)
    pix_key = payload.pix_key.strip()
    transaction = Transaction(company_id=actor.company_id, branch_id=account.branch_id, account_id=account.id, created_by_user_id=actor.id, kind="pix_outgoing", direction="outgoing", amount=payload.amount, currency="BRL", status="pending", idempotency_key=idempotency_key, request_fingerprint=fingerprint, reference=payload.reference, description=payload.description)
    db.add(transaction)
    db.flush()
    pix_transfer = PixTransfer(transaction_id=transaction.id, pix_key_hash=hash_sensitive_value(pix_key), pix_key_last4=pix_key[-4:] if len(pix_key) >= 4 else pix_key, counterparty_name=payload.counterparty_name, counterparty_tax_id=payload.counterparty_tax_id)
    db.add(pix_transfer)
    db.flush()
    audit_event(db, request, action="finance.pix.created", actor=actor, target_type="transaction", target_id=transaction.id, details={"amount": str(transaction.amount), "account_id": str(account.id), "provider_submission": "not_configured"})
    db.commit()
    db.refresh(transaction)
    db.refresh(pix_transfer)
    return _response(transaction, pix_transfer)


@router.get("/transfers/{transaction_id}", response_model=PixTransferOut)
def get_pix_transfer(transaction_id: uuid.UUID, actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.finance, UserRole.accounting)), db: Session = Depends(get_db)) -> PixTransferOut:
    transaction = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.company_id == actor.company_id, Transaction.kind == "pix_outgoing"))
    if not transaction:
        raise HTTPException(status_code=404, detail="Pix transfer not found")
    pix_transfer = db.scalar(select(PixTransfer).where(PixTransfer.transaction_id == transaction.id))
    if not pix_transfer:
        raise HTTPException(status_code=404, detail="Pix transfer not found")
    return _response(transaction, pix_transfer)
