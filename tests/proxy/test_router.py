from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from swarmpot.ledger.dependencies import get_payment_ledger
from swarmpot.ledger.implementations import InMemoryPaymentLedger
from swarmpot.main import app
from swarmpot.proxy.dependencies import get_request_forwarder
from swarmpot.proxy.implementations import FakeRequestForwarder
from swarmpot.proxy.models import TargetBlocked, TargetResponse, TargetUnreachable

from .payments import b64url, signed_payment

URL = "https://api.example.com/thing"


@pytest.fixture
def forwarder() -> FakeRequestForwarder:
    return FakeRequestForwarder()


@pytest.fixture
def client(forwarder: FakeRequestForwarder) -> Iterator[TestClient]:
    app.dependency_overrides[get_request_forwarder] = lambda: forwarder
    app.dependency_overrides[get_payment_ledger] = InMemoryPaymentLedger
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_target_response_is_passed_through(client: TestClient, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(
        status_code=200,
        headers={"content-type": "text/plain", "payment-response": "receipt"},
        body=b"paid content",
    )

    response = client.get("/api/proxy", params={"url": URL, "payment": signed_payment()})

    assert response.status_code == 200
    assert response.text == "paid content"
    assert response.headers["PAYMENT-RESPONSE"] == "receipt"
    assert response.headers["Cache-Control"] == "no-store"
    assert forwarder.sent[0].url == URL


def test_unpaid_post_is_proxied(client: TestClient, forwarder: FakeRequestForwarder) -> None:
    response = client.get("/api/proxy", params={"url": URL, "method": "POST", "body": b64url("hello")})

    assert response.status_code == 200
    assert forwarder.sent[0].method == "POST"
    assert forwarder.sent[0].body == b"hello"
    assert forwarder.sent[0].headers == {}


def test_rejected_payment_402_is_passed_through(client: TestClient, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(
        status_code=402, headers={"payment-required": "requirements"}, body=b'{"error":"insufficient_funds"}'
    )

    response = client.get("/api/proxy", params={"url": URL, "payment": signed_payment()})

    assert response.status_code == 402
    assert response.headers["PAYMENT-REQUIRED"] == "requirements"


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"url": URL, "payment": "not base64!"},
        {"url": URL, "payment": b64url("not json")},
        {"url": URL, "payment": signed_payment(version=3)},
        {"url": "file:///etc/passwd", "payment": signed_payment()},
        {"url": URL, "payment": signed_payment(), "method": "CONNECT"},
        {"url": URL, "payment": signed_payment(), "headers": b64url({"Cookie": "a=b"})},
        {"url": URL, "payment": signed_payment(), "headers": b64url({"PAYMENT-SIGNATURE": "x"})},
    ],
)
def test_malformed_requests_are_rejected_before_forwarding(
    client: TestClient, forwarder: FakeRequestForwarder, params: dict[str, str]
) -> None:
    response = client.get("/api/proxy", params=params)

    assert response.status_code == 422
    assert forwarder.sent == []


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(TargetBlocked("private"), 403), (TargetUnreachable("timed out"), 502)],
)
def test_forwarding_errors_map_to_statuses(
    client: TestClient, forwarder: FakeRequestForwarder, error: Exception, status_code: int
) -> None:
    forwarder.error = error

    response = client.get("/api/proxy", params={"url": URL, "payment": signed_payment()})

    assert response.status_code == status_code
    assert response.json()["detail"] == str(error)


def test_receipt_body_is_json_with_status_200(client: TestClient, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(status_code=402, headers={}, body=b"pay up")

    response = client.get("/api/proxy", params={"url": URL, "receipt": "body"})

    assert response.status_code == 200
    assert response.json()["status"] == 402
    assert response.json()["body"] == "pay up"


def test_unknown_receipt_mode_is_rejected(client: TestClient) -> None:
    assert client.get("/api/proxy", params={"url": URL, "receipt": "json"}).status_code == 422
