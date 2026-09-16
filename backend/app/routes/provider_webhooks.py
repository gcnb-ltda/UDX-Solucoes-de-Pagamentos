import hashlib
import hmac
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Transaction
from app.provider_models import PixCharge, ProviderEvent, ReconciliationRecord
from app.security_controls import audit_event
from app.services.ledger import assert_transaction_balanced, post_pix_incoming

router = APIRouter(prefix="/providers", tags=["provider-webhooks"])


def _verify_signature(body: bytes, timestamp: str, signature: str) -> None:
    secret = settings.payment_provider_webhook_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid webhook timestamp") from exc
    now = int(datetime.now(UTC).timestamp())
    if abs(now - timestamp_value) > settings.webhook_replay_window_seconds:
        raise HTTPException(status_code=401, detail="Webhook timestamp outside replay window")
    message = timestamp.encode() + b"." + body
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


def _decimal(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("invalid provider amount") from exc


@router.post("/{provider}/webhooks")
async def provider_webhook(
    provider: str,
    request: Request,
    x_udx_timestamp: str = Header(alias="X-UDX-Timestamp"),
    x_udx_signature: str = Header(alias="X-UDX-Signature"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    configured_provider = settings.payment_provider.lower().strip()
    if provider != configured_provider or provider == "disabled":
        raise HTTPException(status_code=404, detail="Provider not configured")
    body = await request.body()
    _verify_signature(body, x_udx_timestamp, x_udx_signature)
    try:
        payload = json.loads(body)
        external_event_id = str(payload["id"])
        event_type = str(payload["type"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    existing = db.scalar(
        select(ProviderEvent).where(
            ProviderEvent.provider == provider,
            ProviderEvent.external_event_id == external_event_id,
        )
    )
    if existing:
        return {"status": existing.status, "event_id": str(existing.id)}

    event = ProviderEvent(
        provider=provider,
        external_event_id=external_event_id,
        event_type=event_type,
        payload_sha256=hashlib.sha256(body).hexdigest(),
        payload=payload,
        status="received",
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(
            select(ProviderEvent).where(
                ProviderEvent.provider == provider,
                ProviderEvent.external_event_id == external_event_id,
            )
        )
        if duplicate:
            return {"status": duplicate.status, "event_id": str(duplicate.id)}
        raise

    if event_type != "pix.received":
        event.status = "ignored"
        event.processed_at = datetime.now(UTC)
        db.commit()
        return {"status": event.status, "event_id": str(event.id)}

    data = payload.get("data") or {}
    provider_charge_id = str(data.get("provider_charge_id") or "")
    charge = db.scalar(
        select(PixCharge).where(
            PixCharge.provider == provider,
            PixCharge.provider_charge_id == provider_charge_id,
        )
    )
    if not charge:
        event.status = "unmatched"
        event.processed_at = datetime.now(UTC)
        db.add(
            ReconciliationRecord(
                provider_event_id=event.id,
                status="unmatched",
                provider_amount=_decimal(data.get("amount")) if data.get("amount") is not None else None,
                notes="Provider charge not found",
            )
        )
        db.commit()
        return {"status": event.status, "event_id": str(event.id)}

    transaction = db.scalar(
        select(Transaction).where(Transaction.id == charge.transaction_id).with_for_update()
    )
    if not transaction:
        event.status = "error"
        event.error = "Transaction not found"
        event.processed_at = datetime.now(UTC)
        db.commit()
        return {"status": event.status, "event_id": str(event.id)}

    provider_amount = _decimal(data.get("amount"))
    internal_amount = Decimal(transaction.amount).quantize(Decimal("0.01"))
    difference = provider_amount - internal_amount
    if difference != 0:
        event.status = "mismatch"
        event.processed_at = datetime.now(UTC)
        db.add(
            ReconciliationRecord(
                company_id=transaction.company_id,
                transaction_id=transaction.id,
                provider_event_id=event.id,
                status="mismatch",
                internal_amount=internal_amount,
                provider_amount=provider_amount,
                difference=difference,
                notes="Provider amount differs from internal transaction",
            )
        )
        db.commit()
        return {"status": event.status, "event_id": str(event.id)}

    if transaction.status != "completed":
        post_pix_incoming(db, transaction)
        assert_transaction_balanced(db, transaction.id)
    charge.status = "completed"
    event.status = "processed"
    event.processed_at = datetime.now(UTC)
    db.add(
        ReconciliationRecord(
            company_id=transaction.company_id,
            transaction_id=transaction.id,
            provider_event_id=event.id,
            status="matched",
            internal_amount=internal_amount,
            provider_amount=provider_amount,
            difference=Decimal("0.00"),
        )
    )
    audit_event(
        db,
        request,
        action="finance.pix.received",
        company_id=transaction.company_id,
        target_type="transaction",
        target_id=transaction.id,
        details={"provider": provider, "provider_event_id": external_event_id},
    )
    db.commit()
    return {"status": event.status, "event_id": str(event.id)}
