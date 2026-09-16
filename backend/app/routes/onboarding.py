import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import Branch, Company, User, UserRole
from app.schemas import CompanyOut, UserOut
from app.security import hash_password
from app.security_controls import audit_event

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class BootstrapRequest(BaseModel):
    cnpj: str = Field(pattern=r"^\d{14}$")
    legal_name: str = Field(min_length=2, max_length=180)
    trade_name: str | None = Field(default=None, max_length=180)
    admin_email: EmailStr
    admin_name: str = Field(min_length=2, max_length=160)
    admin_password: str = Field(min_length=12, max_length=128)


class BootstrapResponse(BaseModel):
    company: CompanyOut
    admin: UserOut


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(payload: BootstrapRequest, request: Request, x_bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"), db: Session = Depends(get_db)) -> BootstrapResponse:
    if not x_bootstrap_token or not secrets.compare_digest(x_bootstrap_token, settings.bootstrap_token):
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")
    if db.scalar(select(func.count()).select_from(User)):
        raise HTTPException(status_code=409, detail="Bootstrap already completed")
    company = Company(cnpj=payload.cnpj, legal_name=payload.legal_name, trade_name=payload.trade_name)
    db.add(company)
    db.flush()
    branch = Branch(company_id=company.id, name=payload.trade_name or payload.legal_name, tax_id=payload.cnpj)
    db.add(branch)
    db.flush()
    admin = User(company_id=company.id, email=str(payload.admin_email).lower(), full_name=payload.admin_name, password_hash=hash_password(payload.admin_password), role=UserRole.admin)
    admin.branches.append(branch)
    db.add(admin)
    db.flush()
    audit_event(db, request, action="iam.bootstrap.completed", actor=admin, target_type="company", target_id=company.id, details={"branch_id": str(branch.id)})
    db.commit()
    db.refresh(company)
    db.refresh(admin)
    return BootstrapResponse(company=company, admin=admin)
