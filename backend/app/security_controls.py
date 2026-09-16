import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuditLog, AuthRateLimit, User


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def _rate_key(identity: str) -> str:
    return hashlib.sha256(identity.encode()).hexdigest()


def enforce_rate_limit(
    db: Session,
    *,
    request: Request,
    route: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> None:
    now = datetime.now(UTC)
    bucket_epoch = int(now.timestamp()) // window_seconds * window_seconds
    bucket_start = datetime.fromtimestamp(bucket_epoch, UTC)
    key_hash = _rate_key(f"{_client_ip(request)}|{identity}")

    stmt = (
        insert(AuthRateLimit)
        .values(
            route=route,
            key_hash=key_hash,
            bucket_start=bucket_start,
            attempts=1,
        )
        .on_conflict_do_update(
            constraint="uq_auth_rate_limit_bucket",
            set_={"attempts": AuthRateLimit.attempts + 1},
        )
        .returning(AuthRateLimit.attempts)
    )
    attempts = db.scalar(stmt)
    db.commit()
    if attempts is not None and attempts > limit:
        retry_after = max(
            1,
            int((bucket_start + timedelta(seconds=window_seconds) - now).total_seconds()),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts",
            headers={"Retry-After": str(retry_after)},
        )


def is_temporarily_locked(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > datetime.now(UTC))


def _progressive_lock_minutes(failure_count: int) -> int:
    if failure_count < settings.auth_lock_threshold:
        return 0
    exponent = failure_count - settings.auth_lock_threshold
    return min(settings.auth_lock_max_minutes, 2**exponent)


def register_password_failure(user: User) -> None:
    user.failed_login_count += 1
    lock_minutes = _progressive_lock_minutes(user.failed_login_count)
    if lock_minutes:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=lock_minutes)


def register_mfa_failure(user: User) -> None:
    user.mfa_failed_count += 1
    lock_minutes = _progressive_lock_minutes(user.mfa_failed_count)
    if lock_minutes:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=lock_minutes)


def clear_password_failures(user: User) -> None:
    user.failed_login_count = 0
    if not user.mfa_failed_count:
        user.locked_until = None


def clear_mfa_failures(user: User) -> None:
    user.mfa_failed_count = 0
    if not user.failed_login_count:
        user.locked_until = None


def unlock_user(user: User) -> None:
    user.failed_login_count = 0
    user.mfa_failed_count = 0
    user.locked_until = None


def audit_event(
    db: Session,
    request: Request,
    *,
    action: str,
    actor: User | None = None,
    company_id: uuid.UUID | None = None,
    target_type: str | None = None,
    target_id: str | uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        company_id=company_id or (actor.company_id if actor else None),
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:300] or None,
        details=details or {},
    )
    db.add(event)
    return event
