import pyotp
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_EMAIL = "admin@udx.test"
ADMIN_PASSWORD = "A-Strong-Test-Password-123"


def _bootstrap() -> None:
    response = client.post(
        "/api/v1/onboarding/bootstrap",
        headers={"X-Bootstrap-Token": "test-bootstrap-token"},
        json={
            "cnpj": "29718432000114",
            "legal_name": "GCNB LTDA",
            "trade_name": "UDX Solucoes de Pagamentos",
            "admin_email": ADMIN_EMAIL,
            "admin_name": "UDX Administrator",
            "admin_password": ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 201, response.text


def _login() -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_iam_end_to_end() -> None:
    denied = client.post(
        "/api/v1/onboarding/bootstrap",
        headers={"X-Bootstrap-Token": "wrong"},
        json={
            "cnpj": "29718432000114",
            "legal_name": "GCNB LTDA",
            "admin_email": ADMIN_EMAIL,
            "admin_name": "UDX Administrator",
            "admin_password": ADMIN_PASSWORD,
        },
    )
    assert denied.status_code == 403

    _bootstrap()
    duplicate = client.post(
        "/api/v1/onboarding/bootstrap",
        headers={"X-Bootstrap-Token": "test-bootstrap-token"},
        json={
            "cnpj": "29718432000114",
            "legal_name": "GCNB LTDA",
            "admin_email": ADMIN_EMAIL,
            "admin_name": "UDX Administrator",
            "admin_password": ADMIN_PASSWORD,
        },
    )
    assert duplicate.status_code == 409

    login = _login()
    assert login["mfa_required"] is False
    access = login["tokens"]["access_token"]
    refresh = login["tokens"]["refresh_token"]
    headers = {"Authorization": f"Bearer {access}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    branch = client.post(
        "/api/v1/companies/me/branches",
        headers=headers,
        json={"name": "Filial Sao Paulo", "tax_id": "12345678000199", "address": "Sao Paulo - SP"},
    )
    assert branch.status_code == 201, branch.text
    branch_id = branch.json()["id"]

    new_user = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "finance@udx.test",
            "full_name": "Finance User",
            "password": "Another-Strong-Password-123",
            "role": "finance",
            "branch_ids": [branch_id],
        },
    )
    assert new_user.status_code == 201, new_user.text
    assert new_user.json()["role"] == "finance"

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200, rotated.text
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert replay.status_code == 401

    setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200, setup.text
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()
    confirm = client.post("/api/v1/auth/mfa/confirm", headers=headers, json={"code": code})
    assert confirm.status_code == 204, confirm.text

    mfa_login = _login()
    assert mfa_login["mfa_required"] is True
    assert mfa_login["tokens"] is None
    challenge = mfa_login["challenge_token"]
    verify = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": challenge, "code": pyotp.TOTP(secret).now()},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["access_token"]
