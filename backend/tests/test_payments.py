from fastapi.testclient import TestClient


def test_payment_requires_idempotency_key(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/payments", headers=admin_headers, json={"amount": "100.00", "method": "pix"})
    assert response.status_code == 400


def test_payment_is_persistently_idempotent(client: TestClient, admin_headers: dict[str, str]) -> None:
    headers = {**admin_headers, "Idempotency-Key": "test-payment-001"}
    payload = {"amount": "100.00", "method": "pix", "reference": "ORDER-001"}
    first = client.post("/api/v1/payments", json=payload, headers=headers)
    second = client.post("/api/v1/payments", json=payload, headers=headers)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]


def test_payment_idempotency_rejects_different_payload(client: TestClient, admin_headers: dict[str, str]) -> None:
    headers = {**admin_headers, "Idempotency-Key": "test-payment-conflict"}
    first = client.post("/api/v1/payments", json={"amount": "100.00", "method": "pix"}, headers=headers)
    second = client.post("/api/v1/payments", json={"amount": "101.00", "method": "pix"}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 409
