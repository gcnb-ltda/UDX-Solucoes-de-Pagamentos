import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


class CompanyCreate(BaseModel):
    cnpj: str = Field(pattern=r"^\d{14}$")
    legal_name: str = Field(min_length=2, max_length=180)
    trade_name: str | None = Field(default=None, max_length=180)


class CompanyOut(BaseModel):
    id: uuid.UUID
    cnpj: str
    legal_name: str
    trade_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    tax_id: str | None = Field(default=None, pattern=r"^\d{14}$")
    address: str | None = Field(default=None, max_length=300)


class BranchOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    tax_id: str | None
    address: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = UserRole.cashier
    branch_ids: list[uuid.UUID] = Field(default_factory=list)


class UserOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    mfa_enabled: bool
    failed_login_count: int
    mfa_failed_count: int
    locked_until: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MfaVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(pattern=r"^\d{6}$")


class MfaRecoverRequest(BaseModel):
    challenge_token: str
    recovery_code: str = Field(min_length=8, max_length=32)


class MfaRotateRecoveryRequest(BaseModel):
    password: str
    code: str = Field(pattern=r"^\d{6}$")


class MfaDisableRequest(BaseModel):
    password: str
    code: str = Field(pattern=r"^\d{6}$")


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    mfa_required: bool
    challenge_token: str | None = None
    tokens: TokenPair | None = None


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class MfaRecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]


class MfaConfirmRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="BRL", pattern=r"^BRL$")
    method: str = Field(pattern=r"^(pix|payment_link)$")
    description: str | None = Field(default=None, max_length=200)
    reference: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    method: str
    status: str
    description: str | None = None
    reference: str | None = None
    created_at: datetime


class PaymentAccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    branch_id: uuid.UUID | None = None


class PaymentAccountOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    branch_id: uuid.UUID | None
    name: str
    currency: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PixTransferCreate(BaseModel):
    account_id: uuid.UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    pix_key: str = Field(min_length=3, max_length=160)
    counterparty_name: str | None = Field(default=None, max_length=160)
    counterparty_tax_id: str | None = Field(default=None, pattern=r"^\d{11,14}$")
    description: str | None = Field(default=None, max_length=200)
    reference: str | None = Field(default=None, max_length=100)


class PixTransferOut(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    pix_key_last4: str
    counterparty_name: str | None
    reference: str | None
    created_at: datetime


class TransactionOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    branch_id: uuid.UUID | None
    account_id: uuid.UUID | None
    kind: str
    direction: str
    amount: Decimal
    currency: str
    status: str
    reference: str | None
    description: str | None
    external_id: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    ip_address: str | None
    user_agent: str | None
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TrialBalanceLine(BaseModel):
    ledger_account_id: uuid.UUID
    code: str
    name: str
    account_type: str
    debit: Decimal
    credit: Decimal
    net: Decimal
