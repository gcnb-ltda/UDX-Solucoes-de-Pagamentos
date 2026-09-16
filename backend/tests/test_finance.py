from decimal import Decimal
from fastapi.testclient import TestClient


def _create_account(client: TestClient, admin_headers: dict[str, str]) -> str:
    response = client.post("/api/v1/backoffice/accounts", headers=admin_headers, json={"name":"Conta Operacional UDX"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_pix_persistence_idempotency_and_double_entry_ledger(client: TestClient, admin_headers: dict[str, str]) -> None:
    account_id = _create_account(client, admin_headers)
    headers = {**admin_headers, "Idempotency-Key":"pix-test-001"}
    payload = {"account_id":account_id,"amount":"250.35","pix_key":"beneficiario@example.com","counterparty_name":"Beneficiario Teste","reference":"PAYOUT-001"}
    first = client.post("/api/v1/pix/transfers", headers=headers, json=payload); second = client.post("/api/v1/pix/transfers", headers=headers, json=payload)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["transaction_id"] == second.json()["transaction_id"]
    assert first.json()["status"] == "pending" and "beneficiario@example.com" not in first.text
    transaction_id = first.json()["transaction_id"]
    completed = client.post(f"/api/v1/backoffice/transactions/{transaction_id}/complete", headers=admin_headers, json={"external_id":"SIMULATED-SETTLEMENT-001"})
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    trial_balance = client.get("/api/v1/backoffice/ledger/trial-balance", headers=admin_headers); assert trial_balance.status_code == 200
    debit = sum(Decimal(line["debit"]) for line in trial_balance.json()); credit = sum(Decimal(line["credit"]) for line in trial_balance.json())
    assert debit == credit == Decimal("250.35")
    actions = {event["action"] for event in client.get("/api/v1/backoffice/audit-logs", headers=admin_headers).json()}
    assert {"finance.pix.created","finance.pix.completed_manual"} <= actions


def test_pix_idempotency_conflict(client: TestClient, admin_headers: dict[str, str]) -> None:
    account_id = _create_account(client, admin_headers); headers = {**admin_headers,"Idempotency-Key":"pix-conflict-001"}
    first = client.post("/api/v1/pix/transfers", headers=headers, json={"account_id":account_id,"amount":"50.00","pix_key":"11999999999"})
    second = client.post("/api/v1/pix/transfers", headers=headers, json={"account_id":account_id,"amount":"55.00","pix_key":"11999999999"})
    assert first.status_code == 201 and second.status_code == 409
