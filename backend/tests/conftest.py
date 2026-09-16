import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "A-Strong-Test-Password-123"


@pytest.fixture(autouse=True)
def clean_database():
    table_names = [f'"{table.name}"' for table in Base.metadata.sorted_tables]
    if table_names:
        statement = "TRUNCATE TABLE " + ", ".join(table_names) + " RESTART IDENTITY CASCADE"
        with engine.begin() as connection:
            connection.exec_driver_sql(statement)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def bootstrap_admin(client: TestClient) -> dict:
    response = client.post("/api/v1/onboarding/bootstrap", headers={"X-Bootstrap-Token": "test-bootstrap-token"}, json={"cnpj": "29718432000114", "legal_name": "GCNB LTDA", "trade_name": "UDX Solucoes de Pagamentos", "admin_email": ADMIN_EMAIL, "admin_name": "UDX Administrator", "admin_password": ADMIN_PASSWORD})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def admin_headers(client: TestClient, bootstrap_admin: dict) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
