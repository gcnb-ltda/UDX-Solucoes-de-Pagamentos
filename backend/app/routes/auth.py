import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import RefreshSession, User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MfaConfirmRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.security import (
    create_access_token,
    create_mfa_challenge,
    create_refresh_token,
    create_totp_secret,
    decode_token,
    decrypt_secret,
    encrypt_secret,
    provisioning_uri,
    verify_password,
    verify_totp,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> TokenPair:
    access = create_access_token(user.id, user.company_id, user.role.value)
    refresh, jti, expires_at = create_refresh_token(user.id)
    db.add(RefreshSession(user_id=user.id, jti=jti, expires_at=expires_at))
    user.last_login_at = datetime.now(UTC)
    db.commit()
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_minutes * 60,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not user.is_active or not verify_password(
        payload.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if user.mfa_enabled:
        return LoginResponse(
            mfa_required=True,
            challenge_token=create_mfa_challenge(user.id),
        )
    return LoginResponse(mfa_required=False, tokens=_issue_tokens(db, user))


@router.post("/mfa/verify", response_model=TokenPair)
def verify_mfa(
    payload: MfaVerifyRequest,
    db: Session = Depends(get_db),
) -> TokenPair:
    try:
        claims = decode_token(payload.challenge_token, "mfa_challenge")
        user = db.get(User, uuid.UUID(claims["sub"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid MFA challenge") from exc
    if (
        not user
        or not user.is_active
        or not user.mfa_enabled
        or not user.mfa_secret_encrypted
    ):
        raise HTTPException(status_code=401, detail="MFA unavailable")
    if not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
        user_id = uuid.UUID(claims["sub"])
        jti = claims["jti"]
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    session = db.scalar(select(RefreshSession).where(RefreshSession.jti == jti))
    now = datetime.now(UTC)
    if not session or session.revoked_at or session.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh session invalid")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")
    session.revoked_at = now
    db.commit()
    return _issue_tokens(db, user)


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except ValueError:
        return
    session = db.scalar(
        select(RefreshSession).where(RefreshSession.jti == claims.get("jti"))
    )
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(UTC)
        db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MfaSetupResponse:
    secret = create_totp_secret()
    user.mfa_secret_encrypted = encrypt_secret(secret)
    user.mfa_enabled = False
    db.commit()
    return MfaSetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri(secret, user.email),
    )


@router.post("/mfa/confirm", status_code=204)
def confirm_mfa(
    payload: MfaConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not user.mfa_secret_encrypted:
        raise HTTPException(status_code=400, detail="MFA setup not started")
    if not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    user.mfa_enabled = True
    db.commit()
