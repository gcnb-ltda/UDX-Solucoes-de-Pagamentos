from decimal import Decimal
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/payments", tags=["payments"])

# Armazenamento em memória apenas para o esqueleto inicial do MVP.
# Será substituído por PostgreSQL + ledger persistente.
_idempotency_store: dict[str, dict] = {}


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["BRL"] = "BRL"
    method: Literal["pix", "payment_link"]
    description: str | None = Field(default=None, max_length=200)
    reference: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    id: str
    amount: Decimal
    currency: str
    method: str
    status: Literal["created"]
    description: str | None = None
    reference: str | None = None


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PaymentResponse:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    if idempotency_key in _idempotency_store:
        return PaymentResponse(**_idempotency_store[idempotency_key])

    payment = PaymentResponse(
        id=f"pay_{uuid4().hex}",
        amount=payload.amount,
        currency=payload.currency,
        method=payload.method,
        status="created",
        description=payload.description,
        reference=payload.reference,
    )
    _idempotency_store[idempotency_key] = payment.model_dump()
    return payment
