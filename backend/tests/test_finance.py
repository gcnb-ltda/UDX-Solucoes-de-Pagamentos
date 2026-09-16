import hashlib
import hmac
import json
import time
from decimal import Decimal

from fastapi.testclient import TestClient

WEBHOOK_SECRET = "test-webhook-secret-with-more-than-32-characters"


def _create_account(
    client: TestClient,
    admin_headers: dict[str, str],
) -> str:
    response = client.post(
        "/api/v1/backoffice/accounts",
        headers=admin_headers,
        json={"name": "Conta Operacional UDX"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_and_settle_charge(
    client: TestClient,
    admin_headers: dict[str, str],
    account_id: str,
    amount: str,
    suffix: str,
) -> dict:
    charge = client.post(
        "/api/v1/pix/charges",
        headers={**admin_headers, "Idempotency-Key": f"charge-{suffix}"},
        json={
            "account_id": account_id,
            "amount": amount,
            "reference": f"SALE-{suffix}",
        },
    )
    assert charge.status_code == 201, charge.text
    charge_data = charge.json()

    event = {
        "id": f"evt-{suffix}",
        "type": "pix.received",
        "data": {
            "provider_charge_id": charge_data["provider_charge_id"],
            "amount": amount,
            "end_to_end_id": f"E2E-{suffix}",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    webhook = client.post(
        "/api/v1/providers/mock/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-UDX-Timestamp": timestamp,
            "X-UDX-Signature": signature,
        },
    )
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()["status"] == "processed"
    return charge_data


def test_pix_webhook_reconciliation_and_double_entry_ledger(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    account_id = _create_account(client, admin_headers)
    _create_and_settle_charge(client, admin_headers, account_id, "500.00", "001")

    summary = client.get(
        "/api/v1/backoffice/reconciliation/summary",
        headers=admin_headers,
    )
    assert summary.status_code == 200, summary.text
    assert summary.json()["matched"] == 1

    headers = {**admin_headers, "Idempotency-Key": "pix-test-001"}
    payload = {
        "account_id": account_id,
        "amount": "250.35",
        "pix_key": "beneficiario@example.com",
        "counterparty_name": "Beneficiario Teste",
        "reference": "PAYOUT-001",
    }
    first = client.post("/api/v1/pix/transfers", headers=headers, json=payload)
    second = client.post("/api/v1/pix/transfers", headers=headers, json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["transaction_id"] == second.json()["transaction_id"]
    assert first.json()["status"] == "pending"
    assert first.json()["pix_key_last4"] == ".com"
    assert "beneficiario@example.com" not in first.text

    transaction_id = first.json()["transaction_id"]
    completed = client.post(
        f"/api/v1/backoffice/transactions/{transaction_id}/complete",
        headers=admin_headers,
        json={"external_id": "SIMULATED-SETTLEMENT-001"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"

    trial_balance = client.get(
        "/api/v1/backoffice/ledger/trial-balance",
        headers=admin_headers,
    )
    assert trial_balance.status_code == 200, trial_balance.text
    lines = trial_balance.json()
    debit = sum(Decimal(line["debit"]) for line in lines)
    credit = sum(Decimal(line["credit"]) for line in lines)
    assert debit == Decimal("750.35")
    assert credit == Decimal("750.35")
    assert debit == credit


def test_outgoing_pix_cannot_post_without_customer_funds(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    account_id = _create_account(client, admin_headers)
    transfer = client.post(
        "/api/v1/pix/transfers",
        headers={**admin_headers, "Idempotency-Key": "insufficient-001"},
        json={"account_id": account_id, "amount": "50.00", "pix_key": "11999999999"},
    )
    assert transfer.status_code == 201, transfer.text
    completed = client.post(
        f"/api/v1/backoffice/transactions/{transfer.json()['transaction_id']}/complete",
        headers=admin_headers,
        json={"external_id": "SHOULD-NOT-SETTLE"},
    )
    assert completed.status_code == 409
    assert "insufficient customer funds" in completed.text


def test_webhook_rejects_bad_signature_and_detects_amount_mismatch(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    account_id = _create_account(client, admin_headers)
    charge = client.post(
        "/api/v1/pix/charges",
        headers={**admin_headers, "Idempotency-Key": "charge-mismatch"},
        json={"account_id": account_id, "amount": "100.00"},
    )
    assert charge.status_code == 201, charge.text
    event = {
        "id": "evt-mismatch",
        "type": "pix.received",
        "data": {
            "provider_charge_id": charge.json()["provider_charge_id"],
            "amount": "99.00",
        },
    }
    body = json.dumps(event, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    bad = client.post(
        "/api/v1/providers/mock/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-UDX-Timestamp": timestamp,
            "X-UDX-Signature": "bad-signature",
        },
    )
    assert bad.status_code == 401

    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    mismatch = client.post(
        "/api/v1/providers/mock/webhooks",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-UDX-Timestamp": timestamp,
            "X-UDX-Signature": signature,
        },
    )
    assert mismatch.status_code == 200, mismatch.text
    assert mismatch.json()["status"] == "mismatch"


def test_pix_idempotency_conflict(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    account_id = _create_account(client, admin_headers)
    headers = {**admin_headers, "Idempotency-Key": "pix-conflict-001"}
    first = client.post(
        "/api/v1/pix/transfers",
        headers=headers,
        json={"account_id": account_id, "amount": "50.00", "pix_key": "11999999999"},
    )
    second = client.post(
        "/api/v1/pix/transfers",
        headers=headers,
        json={"account_id": account_id, "amount": "55.00", "pix_key": "11999999999"},
    )
    assert first.status_code == 201
    assert second.status_code == 409
