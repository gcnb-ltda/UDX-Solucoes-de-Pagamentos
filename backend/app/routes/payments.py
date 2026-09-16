import hashlib
import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Transaction, User
from app.schemas import PaymentCreate, PaymentResponse
from app.security_controls import audit_event

router = APIRouter(prefix="/payments", tags=["payments"])


def _fingerprint(payload: PaymentCreate) -> str:
    raw = json.dumps({"amount": str(payload.amount.quantize(Decimal("0.01"))), "currency": payload.currency, "method": payload.method, "description": payload.description, "reference": payload.reference}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _response(transaction: Transaction) -> PaymentResponse:
    return PaymentResponse(id=transaction.id, amount=transaction.amount, currency=transaction.currency, method=transaction.kind, status=transaction.status, description=transaction.description, reference=transaction.reference, created_at=transaction.created_at)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PaymentResponse:
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required")
    if len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="Idempotency-Key is too long")
    fingerprint = _fingerprint(payload)
    existing = db.scalar(select(Transaction).where(Transaction.company_id == actor.company_id, Transaction.idempotency_key == idempotency_key))
    if existing:
        if existing.request_fingerprint != fingerprint:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency-Key already used with different payload")
        return _response(existing)
    transaction = Transaction(company_id=actor.company_id, created_by_user_id=actor.id, kind=payload.method, direction="incoming", amount=payload.amount, currency=payload.currency, status="created", idempotency_key=idempotency_key, request_fingerprint=fingerprint, description=payload.description, reference=payload.reference)
    db.add(transaction)
    db.flush()
    audit_event(db, request, action="payments.transaction.created", actor=actor, target_type="transaction", target_id=transaction.id, details={"kind": transaction.kind, "amount": str(transaction.amount)})
    db.commit()
    db.refresh(transaction)
    return _response(transaction)
