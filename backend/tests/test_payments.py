from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_payment_requires_idempotency_key() -> None:
    response = client.post(
        "/api/v1/payments",
        json={"amount": "100.00", "method": "pix"},
    )
    assert response.status_code == 400


def test_payment_is_idempotent() -> None:
    headers = {"Idempotency-Key": "test-payment-001"}
    payload = {"amount": "100.00", "method": "pix", "reference": "ORDER-001"}

    first = client.post("/api/v1/payments", json=payload, headers=headers)
    second = client.post("/api/v1/payments", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
