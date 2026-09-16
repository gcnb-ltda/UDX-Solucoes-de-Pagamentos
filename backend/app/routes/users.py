import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models import Branch, User, UserRole
from app.schemas import UserCreate, UserOut
from app.security import hash_password

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
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    branches: list[Branch] = []
    if payload.branch_ids:
        branches = list(
            db.scalars(
                select(Branch).where(
                    Branch.id.in_(payload.branch_ids),
                    Branch.company_id == actor.company_id,
                    Branch.is_active.is_(True),
                )
            )
        )
        if len(branches) != len(set(payload.branch_ids)):
            raise HTTPException(status_code=400, detail="Invalid branch assignment")

    user = User(
        company_id=actor.company_id,
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    user.branches.extend(branches)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: uuid.UUID,
    actor: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    if actor.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user = db.scalar(select(User).where(User.id == user_id, User.company_id == actor.company_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
