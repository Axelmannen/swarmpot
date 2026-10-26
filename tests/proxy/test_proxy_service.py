import base64
import json

import pytest

from swarmpot.ledger.implementations import InMemoryPaymentLedger
from swarmpot.proxy.application import ProxyService
from swarmpot.proxy.implementations import FakeRequestForwarder
from swarmpot.proxy.models import ProxyRequest, TargetResponse

from .payments import b64url, receipt, signed_payment

pytestmark = pytest.mark.anyio

URL = "https://api.example.com/v1/generate?model=small"


@pytest.fixture
def forwarder() -> FakeRequestForwarder:
    return FakeRequestForwarder()


@pytest.fixture
def ledger() -> InMemoryPaymentLedger:
    return InMemoryPaymentLedger()


@pytest.fixture
def service(forwarder: FakeRequestForwarder, ledger: InMemoryPaymentLedger) -> ProxyService:
    return ProxyService(forwarder, ledger)


async def test_v2_payment_is_sent_as_payment_signature(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    payment = signed_payment(version=2)

    await service.forward(ProxyRequest(url=URL, payment=payment))

    [sent] = forwarder.sent
    assert sent.method == "GET"
    assert sent.url == URL
    assert sent.headers == {"PAYMENT-SIGNATURE": payment}
    assert sent.body is None


async def test_request_without_payment_is_forwarded_as_is(
    service: ProxyService, forwarder: FakeRequestForwarder
) -> None:
    await service.forward(
        ProxyRequest(url=URL, method="POST", body=b64url('{"q":1}'), headers=b64url({"Accept": "application/json"}))
    )

    [sent] = forwarder.sent
    assert sent.method == "POST"
    assert sent.headers == {"Accept": "application/json"}
    assert sent.body == b'{"q":1}'


async def test_v1_payment_is_sent_as_x_payment(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    await service.forward(ProxyRequest(url=URL, payment=signed_payment(version=1)))

    assert list(forwarder.sent[0].headers) == ["X-PAYMENT"]


async def test_url_safe_payment_is_forwarded_as_standard_base64(
    service: ProxyService, forwarder: FakeRequestForwarder
) -> None:
    payment = signed_payment(note="needs padding and ??>>")
    url_safe = payment.replace("+", "-").replace("/", "_").rstrip("=")
    assert url_safe != payment

    await service.forward(ProxyRequest(url=URL, payment=url_safe))

    assert forwarder.sent[0].headers["PAYMENT-SIGNATURE"] == payment
    base64.b64decode(payment, validate=True)


async def test_method_body_and_headers_are_rebuilt(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    await service.forward(
        ProxyRequest(
            url=URL,
            payment=signed_payment(),
            method="POST",
            body=b64url('{"prompt":"hello"}'),
            headers=b64url({"Content-Type": "application/json"}),
        )
    )

    [sent] = forwarder.sent
    assert sent.method == "POST"
    assert sent.body == b'{"prompt":"hello"}'
    assert sent.headers["Content-Type"] == "application/json"


async def test_only_safe_response_headers_are_returned(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(
        status_code=200,
        headers={
            "content-type": "application/json",
            "payment-response": "receipt",
            "set-cookie": "session=abc",
            "content-encoding": "gzip",
            "cache-control": "public, max-age=3600",
        },
        body=b"{}",
    )

    response = await service.forward(ProxyRequest(url=URL, payment=signed_payment()))

    assert response.headers == {
        "content-type": "application/json",
        "payment-response": "receipt",
        "cache-control": "no-store",
        "referrer-policy": "no-referrer",
    }
    assert response.body == b"{}"


V2_PAYMENT = signed_payment(
    accepted={"network": "eip155:84532", "amount": "10000", "asset": "0xUSDC"},
    payload={"authorization": {"from": "0xpayer", "value": "10000"}},
)


async def test_settled_payment_is_recorded_by_host(
    service: ProxyService, forwarder: FakeRequestForwarder, ledger: InMemoryPaymentLedger
) -> None:
    forwarder.response = TargetResponse(
        status_code=200, headers={"payment-response": receipt(transaction="0xtx")}, body=b"paid"
    )

    await service.forward(ProxyRequest(url=URL, payment=V2_PAYMENT))

    [recorded] = ledger.payments.values()
    assert (recorded.host, recorded.network, recorded.asset, recorded.amount, recorded.transaction) == (
        "api.example.com",
        "eip155:84532",
        "0xUSDC",
        "10000",
        "0xtx",
    )


async def test_v1_receipt_is_recorded_with_amount_from_authorization(
    service: ProxyService, forwarder: FakeRequestForwarder, ledger: InMemoryPaymentLedger
) -> None:
    forwarder.response = TargetResponse(
        status_code=200, headers={"x-payment-response": receipt(network="base-sepolia")}, body=b"paid"
    )
    payment = signed_payment(version=1, network="base-sepolia", payload={"authorization": {"value": "500"}})

    await service.forward(ProxyRequest(url=URL, payment=payment))

    [recorded] = ledger.payments.values()
    assert (recorded.network, recorded.asset, recorded.amount) == ("base-sepolia", None, "500")


@pytest.mark.parametrize(
    "response",
    [
        TargetResponse(status_code=200, headers={}, body=b""),
        TargetResponse(status_code=200, headers={"payment-response": receipt(success=False)}, body=b""),
        TargetResponse(status_code=500, headers={"payment-response": receipt()}, body=b""),
        TargetResponse(status_code=200, headers={"payment-response": "not base64 json"}, body=b""),
    ],
)
async def test_unsettled_payment_is_not_recorded(
    service: ProxyService, forwarder: FakeRequestForwarder, ledger: InMemoryPaymentLedger, response: TargetResponse
) -> None:
    forwarder.response = response

    await service.forward(ProxyRequest(url=URL, payment=V2_PAYMENT))

    assert ledger.payments == {}


async def test_receipt_without_payment_is_not_recorded(
    service: ProxyService, forwarder: FakeRequestForwarder, ledger: InMemoryPaymentLedger
) -> None:
    forwarder.response = TargetResponse(status_code=200, headers={"payment-response": receipt()}, body=b"")

    await service.forward(ProxyRequest(url=URL))

    assert ledger.payments == {}


async def test_receipt_body_wraps_a_paid_response(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(
        status_code=200,
        headers={"content-type": "text/html", "payment-response": receipt(transaction="0xtx"), "set-cookie": "a=b"},
        body=b"<p>paid</p>",
    )

    response = await service.forward(ProxyRequest(url=URL, payment=V2_PAYMENT, receipt="body"))

    assert response.status_code == 200
    assert response.headers == {
        "content-type": "application/json",
        "cache-control": "no-store",
        "referrer-policy": "no-referrer",
    }
    assert json.loads(response.body) == {
        "status": 200,
        "content_type": "text/html",
        "receipt": {"success": True, "transaction": "0xtx", "network": "eip155:84532", "payer": "0xpayer"},
        "payment_required": None,
        "body": "<p>paid</p>",
        "body_encoding": "text",
    }


async def test_receipt_body_turns_a_402_into_200_with_the_reason(
    service: ProxyService, forwarder: FakeRequestForwarder
) -> None:
    required = base64.b64encode(json.dumps({"x402Version": 2, "error": "insufficient_funds"}).encode()).decode()
    forwarder.response = TargetResponse(status_code=402, headers={"payment-required": required}, body=b"{}")

    response = await service.forward(ProxyRequest(url=URL, payment=V2_PAYMENT, receipt="body"))

    wrapped = json.loads(response.body)
    assert response.status_code == 200
    assert (wrapped["status"], wrapped["receipt"]) == (402, None)
    assert wrapped["payment_required"]["error"] == "insufficient_funds"


async def test_receipt_body_base64_encodes_binary(service: ProxyService, forwarder: FakeRequestForwarder) -> None:
    forwarder.response = TargetResponse(status_code=200, headers={"content-type": "image/png"}, body=b"\x89PNG\xff")

    wrapped = json.loads((await service.forward(ProxyRequest(url=URL, receipt="body"))).body)

    assert wrapped["body_encoding"] == "base64"
    assert base64.b64decode(wrapped["body"]) == b"\x89PNG\xff"
