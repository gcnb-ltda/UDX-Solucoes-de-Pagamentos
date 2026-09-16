from datetime import UTC, datetime

import jwt
import pyotp
from conftest import ADMIN_EMAIL, ADMIN_PASSWORD
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.secrets import get_active_jwt_kid, get_jwt_key_ring
from app.db import SessionLocal
from app.models import User
from app.security import create_access_token, decode_token


def test_jwt_uses_active_kid_and_rejects_unknown_key(
    client: TestClient,
    bootstrap_admin: dict,
) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        assert user is not None
        token = create_access_token(user.id, user.company_id, user.role.value)

    header = jwt.get_unverified_header(token)
    assert header["kid"] == get_active_jwt_kid()
    assert decode_token(token, "access")["sub"]

    forged = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "type": "access",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "exp": int(datetime.now(UTC).timestamp()) + 300,
        },
        list(get_jwt_key_ring().values())[0],
        algorithm=settings.jwt_algorithm,
        headers={"kid": "retired-key"},
    )
    try:
        decode_token(forged, "access")
    except ValueError:
        pass
    else:
        raise AssertionError("token signed with unknown kid must be rejected")


def test_login_rate_limit(client: TestClient) -> None:
    for _ in range(settings.auth_login_rate_limit):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_progressive_lockout_blocks_valid_password(
    client: TestClient,
    bootstrap_admin: dict,
) -> None:
    for _ in range(settings.auth_lock_threshold):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrong-password"},
        )
        assert response.status_code == 401

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        assert user is not None
        assert user.failed_login_count == settings.auth_lock_threshold
        assert user.locked_until is not None
        assert user.locked_until > datetime.now(UTC)

    valid = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert valid.status_code == 401


def test_mfa_recovery_code_is_single_use(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    setup = client.post("/api/v1/auth/mfa/setup", headers=admin_headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    recovery_code = setup.json()["recovery_codes"][0]

    confirm = client.post(
        "/api/v1/auth/mfa/confirm",
        headers=admin_headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert confirm.status_code == 204, confirm.text

    first_login = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    challenge = first_login.json()["challenge_token"]
    recovered = client.post(
        "/api/v1/auth/mfa/recover",
        json={"challenge_token": challenge, "recovery_code": recovery_code},
    )
    assert recovered.status_code == 200, recovered.text

    second_login = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    challenge2 = second_login.json()["challenge_token"]
    replay = client.post(
        "/api/v1/auth/mfa/recover",
        json={"challenge_token": challenge2, "recovery_code": recovery_code},
    )
    assert replay.status_code == 401


def test_key_status_never_exposes_key_material(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/auth/keys/status", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_kid"]
    serialized = str(payload)
    for key in get_jwt_key_ring().values():
        assert key not in serialized
