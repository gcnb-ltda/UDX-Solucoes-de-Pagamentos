import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.secrets import jwt_key_status
from app.db import get_db
from app.dependencies import get_current_user, require_roles
from app.models import MfaRecoveryCode, RefreshSession, User, UserRole
from app.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MfaConfirmRequest,
    MfaDisableRequest,
    MfaRecoverRequest,
    MfaRecoveryCodesResponse,
    MfaRotateRecoveryRequest,
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
    generate_recovery_codes,
    hash_recovery_code,
    provisioning_uri,
    verify_password,
    verify_recovery_code,
    verify_totp,
)
from app.security_controls import (
    audit_event,
    clear_mfa_failures,
    clear_password_failures,
    enforce_rate_limit,
    is_temporarily_locked,
    register_mfa_failure,
    register_password_failure,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> TokenPair:
    access = create_access_token(user.id, user.company_id, user.role.value)
    refresh, jti, expires_at = create_refresh_token(user.id)
    db.add(RefreshSession(user_id=user.id, jti=jti, expires_at=expires_at))
    user.last_login_at = datetime.now(UTC)
    db.flush()
    return TokenPair(access_token=access, refresh_token=refresh, expires_in=settings.jwt_access_minutes * 60)


def _store_recovery_codes(db: Session, user: User, codes: list[str]) -> None:
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    db.add_all([MfaRecoveryCode(user_id=user.id, code_hash=hash_recovery_code(code)) for code in codes])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> LoginResponse:
    email = str(payload.email).lower()
    enforce_rate_limit(db, request=request, route="login", identity=email, limit=settings.auth_login_rate_limit, window_seconds=settings.auth_login_rate_window_seconds)
    user = db.scalar(select(User).where(User.email == email))
    if user and is_temporarily_locked(user):
        audit_event(db, request, action="auth.login.locked", actor=user, target_type="user", target_id=user.id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active or not verify_password(payload.password, user.password_hash):
        if user.is_active:
            register_password_failure(user)
            audit_event(db, request, action="auth.login.failed", actor=user, target_type="user", target_id=user.id, details={"stage": "password"})
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    clear_password_failures(user)
    if user.mfa_enabled:
        challenge = create_mfa_challenge(user.id)
        audit_event(db, request, action="auth.login.mfa_challenge", actor=user, target_type="user", target_id=user.id)
        db.commit()
        return LoginResponse(mfa_required=True, challenge_token=challenge)
    tokens = _issue_tokens(db, user)
    audit_event(db, request, action="auth.login.success", actor=user, target_type="user", target_id=user.id, details={"mfa": False})
    db.commit()
    return LoginResponse(mfa_required=False, tokens=tokens)


@router.post("/mfa/verify", response_model=TokenPair)
def verify_mfa(payload: MfaVerifyRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    enforce_rate_limit(db, request=request, route="mfa_verify", identity=payload.challenge_token, limit=settings.auth_mfa_rate_limit, window_seconds=settings.auth_mfa_rate_window_seconds)
    try:
        claims = decode_token(payload.challenge_token, "mfa_challenge")
        user = db.get(User, uuid.UUID(claims["sub"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid MFA challenge") from exc
    if not user or not user.is_active or not user.mfa_enabled or not user.mfa_secret_encrypted or is_temporarily_locked(user):
        raise HTTPException(status_code=401, detail="MFA unavailable")
    if not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        register_mfa_failure(user)
        audit_event(db, request, action="auth.mfa.failed", actor=user, target_type="user", target_id=user.id, details={"method": "totp"})
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    clear_mfa_failures(user)
    tokens = _issue_tokens(db, user)
    audit_event(db, request, action="auth.login.success", actor=user, target_type="user", target_id=user.id, details={"mfa": True, "method": "totp"})
    db.commit()
    return tokens


@router.post("/mfa/recover", response_model=TokenPair)
def recover_mfa(payload: MfaRecoverRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    enforce_rate_limit(db, request=request, route="mfa_recover", identity=payload.challenge_token, limit=settings.auth_mfa_rate_limit, window_seconds=settings.auth_mfa_rate_window_seconds)
    try:
        claims = decode_token(payload.challenge_token, "mfa_challenge")
        user = db.get(User, uuid.UUID(claims["sub"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid MFA challenge") from exc
    if not user or not user.is_active or not user.mfa_enabled or is_temporarily_locked(user):
        raise HTTPException(status_code=401, detail="MFA unavailable")
    recovery_codes = list(db.scalars(select(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id, MfaRecoveryCode.used_at.is_(None))))
    matched = next((recovery for recovery in recovery_codes if verify_recovery_code(payload.recovery_code, recovery.code_hash)), None)
    if not matched:
        register_mfa_failure(user)
        audit_event(db, request, action="auth.mfa.failed", actor=user, target_type="user", target_id=user.id, details={"method": "recovery_code"})
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid recovery code")
    matched.used_at = datetime.now(UTC)
    clear_mfa_failures(user)
    tokens = _issue_tokens(db, user)
    audit_event(db, request, action="auth.mfa.recovery_used", actor=user, target_type="user", target_id=user.id)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
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
    if not user or not user.is_active or is_temporarily_locked(user):
        raise HTTPException(status_code=401, detail="User inactive")
    session.revoked_at = now
    tokens = _issue_tokens(db, user)
    audit_event(db, request, action="auth.refresh.rotated", actor=user, target_type="refresh_session", target_id=session.id)
    db.commit()
    return tokens


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, request: Request, db: Session = Depends(get_db)) -> None:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except ValueError:
        return
    session = db.scalar(select(RefreshSession).where(RefreshSession.jti == claims.get("jti")))
    if session and not session.revoked_at:
        session.revoked_at = datetime.now(UTC)
        user = db.get(User, session.user_id)
        audit_event(db, request, action="auth.logout", actor=user, target_type="refresh_session", target_id=session.id)
        db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def setup_mfa(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MfaSetupResponse:
    secret = create_totp_secret()
    recovery_codes = generate_recovery_codes()
    user.mfa_secret_encrypted = encrypt_secret(secret)
    user.mfa_enabled = False
    _store_recovery_codes(db, user, recovery_codes)
    audit_event(db, request, action="iam.mfa.setup_started", actor=user, target_type="user", target_id=user.id)
    db.commit()
    return MfaSetupResponse(secret=secret, provisioning_uri=provisioning_uri(secret, user.email), recovery_codes=recovery_codes)


@router.post("/mfa/confirm", status_code=204)
def confirm_mfa(payload: MfaConfirmRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not user.mfa_secret_encrypted:
        raise HTTPException(status_code=400, detail="MFA setup not started")
    if not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        register_mfa_failure(user)
        audit_event(db, request, action="iam.mfa.confirm_failed", actor=user, target_type="user", target_id=user.id)
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    user.mfa_enabled = True
    clear_mfa_failures(user)
    audit_event(db, request, action="iam.mfa.enabled", actor=user, target_type="user", target_id=user.id)
    db.commit()


@router.post("/mfa/recovery-codes/rotate", response_model=MfaRecoveryCodesResponse)
def rotate_recovery_codes(payload: MfaRotateRecoveryRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MfaRecoveryCodesResponse:
    if not user.mfa_enabled or not user.mfa_secret_encrypted or not verify_password(payload.password, user.password_hash) or not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        raise HTTPException(status_code=401, detail="MFA verification failed")
    codes = generate_recovery_codes()
    _store_recovery_codes(db, user, codes)
    audit_event(db, request, action="iam.mfa.recovery_codes_rotated", actor=user, target_type="user", target_id=user.id)
    db.commit()
    return MfaRecoveryCodesResponse(recovery_codes=codes)


@router.post("/mfa/disable", status_code=204)
def disable_mfa(payload: MfaDisableRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not user.mfa_enabled or not user.mfa_secret_encrypted or not verify_password(payload.password, user.password_hash) or not verify_totp(decrypt_secret(user.mfa_secret_encrypted), payload.code):
        raise HTTPException(status_code=401, detail="MFA verification failed")
    user.mfa_enabled = False
    user.mfa_secret_encrypted = None
    db.execute(delete(MfaRecoveryCode).where(MfaRecoveryCode.user_id == user.id))
    db.execute(update(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
    audit_event(db, request, action="iam.mfa.disabled", actor=user, target_type="user", target_id=user.id)
    db.commit()


@router.get("/keys/status")
def keys_status(_: User = Depends(require_roles(UserRole.admin))) -> dict[str, object]:
    return jwt_key_status()
