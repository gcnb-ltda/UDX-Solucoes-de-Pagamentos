import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models import PaymentAccount, Transaction, User, UserRole
from app.provider_models import PixCharge
from app.security_controls import audit_event
from app.services.provider import ProviderUnavailable, get_payment_provider

router = APIRouter(prefix="/pix/charges", tags=["pix"])


class PixChargeCreate(BaseModel):
    account_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    description: str | None = Field(default=None, max_length=200)
    reference: str | None = Field(default=None, max_length=100)
    expires_in_seconds: int = Field(default=900, ge=60, le=86400)


class PixChargeOut(BaseModel):
    transaction_id: uuid.UUID
    provider: str
    provider_charge_id: str
    txid: str | None
    copy_paste: str | None
    amount: Decimal
    currency: str
    status: str
    expires_at: datetime | None


def _fingerprint(payload: PixChargeCreate) -> str:
    raw = json.dumps(
        {
            "account_id": str(payload.account_id),
            "amount": str(payload.amount.quantize(Decimal("0.01"))),
            "description": payload.description,
            "reference": payload.reference,
            "expires_in_seconds": payload.expires_in_seconds,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _response(transaction: Transaction, charge: PixCharge) -> PixChargeOut:
    return PixChargeOut(
        transaction_id=transaction.id,
        provider=charge.provider,
        provider_charge_id=charge.provider_charge_id,
        txid=charge.txid,
        copy_paste=charge.copy_paste,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        expires_at=charge.expires_at,
    )


@router.post("", response_model=PixChargeOut, status_code=status.HTTP_201_CREATED)
def create_pix_charge(
    payload: PixChargeCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: User = Depends(require_roles(UserRole.admin, UserRole.manager, UserRole.finance, UserRole.cashier)),
    db: Session = Depends(get_db),
) -> PixChargeOut:
    if not idempotency_key or len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="Valid Idempotency-Key header is required")
    account = db.scalar(
        select(PaymentAccount).where(
            PaymentAccount.id == payload.account_id,
            PaymentAccount.company_id == actor.company_id,
            PaymentAccount.status == "active",
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")

    fingerprint = _fingerprint(payload)
    existing = db.scalar(
        select(Transaction).where(
            Transaction.company_id == actor.company_id,
            Transaction.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if existing.request_fingerprint != fingerprint or existing.kind != "pix_charge":
            raise HTTPException(status_code=409, detail="Idempotency-Key conflict")
        charge = db.scalar(select(PixCharge).where(PixCharge.transaction_id == existing.id))
        if not charge:
            raise HTTPException(status_code=409, detail="Incomplete idempotent Pix charge")
        return _response(existing, charge)

    try:
        provider = get_payment_provider()
        provider_result = provider.create_pix_charge(
            amount=payload.amount,
            reference=payload.reference,
            idempotency_key=idempotency_key,
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    transaction = Transaction(
        company_id=actor.company_id,
        branch_id=account.branch_id,
        account_id=account.id,
        created_by_user_id=actor.id,
        kind="pix_charge",
        direction="incoming",
        amount=payload.amount,
        currency="BRL",
        status="pending",
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        reference=payload.reference,
        description=payload.description,
        external_id=provider_result.provider_charge_id,
    )
    db.add(transaction)
    db.flush()
    charge = PixCharge(
        transaction_id=transaction.id,
        provider=provider_result.provider,
        provider_charge_id=provider_result.provider_charge_id,
        txid=provider_result.txid,
        copy_paste=provider_result.copy_paste,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(seconds=payload.expires_in_seconds),
    )
    db.add(charge)
    db.flush()
    audit_event(
        db,
        request,
        action="finance.pix.charge.created",
        actor=actor,
        target_type="transaction",
        target_id=transaction.id,
        details={"provider": charge.provider, "account_id": str(account.id)},
    )
    db.commit()
    db.refresh(transaction)
    db.refresh(charge)
    return _response(transaction, charge)
