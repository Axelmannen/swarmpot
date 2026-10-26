from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from swarmpot.ledger.dependencies import get_payment_ledger
from swarmpot.ledger.implementations import InMemoryPaymentLedger
from swarmpot.ledger.models import SettledPayment
from swarmpot.main import app


@pytest.fixture
def ledger() -> InMemoryPaymentLedger:
    return InMemoryPaymentLedger()


@pytest.fixture
def client(ledger: InMemoryPaymentLedger) -> Iterator[TestClient]:
    app.dependency_overrides[get_payment_ledger] = lambda: ledger
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_overview_lists_sites_and_recent_payments(client: TestClient, ledger: InMemoryPaymentLedger) -> None:
    ledger.payments["0xtx"] = SettledPayment(
        host="api.example.com",
        network="eip155:8453",
        asset="0xUSDC",
        amount="10000",
        transaction="0xtx",
        settled_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    response = client.get("/api/payments")

    assert response.status_code == 200
    body = response.json()
    assert body["sites"] == [
        {
            "host": "api.example.com",
            "network": "eip155:8453",
            "asset": "0xUSDC",
            "payments": 1,
            "total": "10000",
            "last_settled_at": "2026-10-01T00:00:00Z",
        }
    ]
    assert [p["transaction"] for p in body["recent"]] == ["0xtx"]
    assert "payer" not in body["recent"][0]


def test_empty_ledger(client: TestClient) -> None:
    assert client.get("/api/payments").json() == {"sites": [], "recent": []}
