import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import pyotp
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.app_secret_key.encode()).digest()
    import base64

    return Fernet(base64.urlsafe_b64encode(digest))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def create_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="UDX Payments")


def _encode(subject: str, token_type: str, expires_delta: timedelta, **claims: object) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = secrets.token_hex(16)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        **claims,
    }
    token = jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def create_access_token(user_id: uuid.UUID, company_id: uuid.UUID, role: str) -> str:
    token, _, _ = _encode(
        str(user_id),
        "access",
        timedelta(minutes=settings.jwt_access_minutes),
        company_id=str(company_id),
        role=role,
    )
    return token


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    return _encode(str(user_id), "refresh", timedelta(days=settings.jwt_refresh_days))


def create_mfa_challenge(user_id: uuid.UUID) -> str:
    token, _, _ = _encode(
        str(user_id),
        "mfa_challenge",
        timedelta(minutes=settings.jwt_mfa_challenge_minutes),
    )
    return token


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except JWTError as exc:
        raise ValueError("invalid token") from exc
    if payload.get("type") != expected_type:
        raise ValueError("invalid token type")
    return payload
