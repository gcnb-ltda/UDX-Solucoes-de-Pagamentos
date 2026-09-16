import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Branch, Company, User, UserRole
from app.schemas import BranchCreate, BranchOut, CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/me", response_model=CompanyOut)
def get_company(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Company:
    company = db.get(Company, user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/me/branches", response_model=list[BranchOut])
def list_branches(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Branch]:
    return list(
        db.scalars(
            select(Branch).where(Branch.company_id == user.company_id).order_by(Branch.name)
        )
    )


@router.post("/me/branches", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    db: Session = Depends(get_db),
) -> Branch:
    branch = Branch(
        company_id=user.company_id,
        name=payload.name,
        tax_id=payload.tax_id,
        address=payload.address,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.patch("/me/branches/{branch_id}/deactivate", response_model=BranchOut)
def deactivate_branch(
    branch_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> Branch:
    branch = db.scalar(
        select(Branch).where(Branch.id == branch_id, Branch.company_id == user.company_id)
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    branch.is_active = False
    db.commit()
    db.refresh(branch)
    return branch
