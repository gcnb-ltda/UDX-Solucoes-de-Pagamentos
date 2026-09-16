import uuid
from datetime import datetime

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
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MfaVerifyRequest(BaseModel):
    challenge_token: str
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


class MfaConfirmRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")
