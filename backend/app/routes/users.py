import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models import Branch, RefreshSession, User, UserRole
from app.schemas import UserCreate, UserOut
from app.security import hash_password
from app.security_controls import audit_event, unlock_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    actor: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.scalars(select(User).where(User.company_id == actor.company_id).order_by(User.full_name)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    branches: list[Branch] = []
    if payload.branch_ids:
        branches = list(db.scalars(select(Branch).where(Branch.id.in_(payload.branch_ids), Branch.company_id == actor.company_id, Branch.is_active.is_(True))))
        if len(branches) != len(set(payload.branch_ids)):
            raise HTTPException(status_code=400, detail="Invalid branch assignment")
    user = User(company_id=actor.company_id, email=email, full_name=payload.full_name, password_hash=hash_password(payload.password), role=payload.role)
    user.branches.extend(branches)
    db.add(user)
    db.flush()
    audit_event(db, request, action="iam.user.created", actor=actor, target_type="user", target_id=user.id, details={"role": user.role.value, "branch_ids": [str(branch.id) for branch in branches]})
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    if actor.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = db.scalar(select(User).where(User.id == user_id, User.company_id == actor.company_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.execute(update(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
    audit_event(db, request, action="iam.user.deactivated", actor=actor, target_type="user", target_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/unlock", response_model=UserOut)
def admin_unlock_user(
    user_id: uuid.UUID,
    request: Request,
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.company_id == actor.company_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    unlock_user(user)
    audit_event(db, request, action="iam.user.unlocked", actor=actor, target_type="user", target_id=user.id)
    db.commit()
    db.refresh(user)
    return user
