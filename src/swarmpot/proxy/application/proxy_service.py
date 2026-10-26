import base64
import binascii
import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.ledger.models import SettledPayment
from swarmpot.proxy.interfaces import RequestForwarder
from swarmpot.proxy.models import OutboundRequest, ProxyRequest, TargetResponse, WrappedResponse

# Where each x402 version expects the signed payment.
PAYMENT_HEADERS = {1: "X-PAYMENT", 2: "PAYMENT-SIGNATURE"}

# Where each x402 version puts the settlement receipt.
RECEIPT_HEADERS = ("payment-response", "x-payment-response")

# Target response headers passed back to the caller: the content type, redirect/retry hints, and
# the x402 headers (requirements on a 402, the settlement receipt on success).
RETURNED_HEADERS = ("content-type", "location", "retry-after", "payment-required", *RECEIPT_HEADERS)

# The request URL carries a spendable payment, so keep it out of caches and Referer headers.
PRIVACY_HEADERS = {"cache-control": "no-store", "referrer-policy": "no-referrer"}


class ProxyService:
    def __init__(self, forwarder: RequestForwarder, ledger: PaymentLedger) -> None:
        self._forwarder = forwarder
        self._ledger = ledger

    async def forward(self, request: ProxyRequest) -> TargetResponse:
        """Send the request to its target, with the payment attached if there is one, and return what the caller should see.

        The proxy never verifies or settles the payment: the target does. Its answer, including a 402
        that rejects the payment, is passed back as is. When the target reports a settled payment, it
        goes in the public ledger. With receipt=body the answer is wrapped in JSON (see WrappedResponse).
        """
        headers = request.decoded_headers()
        version, payment = request.payment_version(), request.payment_header_value()
        if version is not None and payment is not None:
            headers[PAYMENT_HEADERS[version]] = payment
        response = await self._forwarder.send(
            OutboundRequest(method=request.method, url=request.url, headers=headers, body=request.decoded_body())
        )
        if settled := _settled_payment(request, response):
            await self._ledger.record(settled)
        if request.receipt == "body":
            headers = {"content-type": "application/json"} | PRIVACY_HEADERS
            return TargetResponse(status_code=200, headers=headers, body=_wrap(response).model_dump_json().encode())
        headers = {name: value for name, value in response.headers.items() if name in RETURNED_HEADERS}
        return response.model_copy(update={"headers": headers | PRIVACY_HEADERS})


def _wrap(response: TargetResponse) -> WrappedResponse:
    try:
        body, encoding = response.body.decode(), "text"
    except UnicodeDecodeError:
        body, encoding = base64.b64encode(response.body).decode(), "base64"
    return WrappedResponse(
        status=response.status_code,
        content_type=response.headers.get("content-type"),
        receipt=_receipt(response),
        payment_required=_decode_json(response.headers["payment-required"])
        if "payment-required" in response.headers
        else None,
        body=body,
        body_encoding=encoding,
    )


def _receipt(response: TargetResponse) -> dict[str, Any] | None:
    return next((_decode_json(response.headers[h]) for h in RECEIPT_HEADERS if h in response.headers), None)


def _settled_payment(request: ProxyRequest, response: TargetResponse) -> SettledPayment | None:
    """The payment the target says it settled, or None when there was no payment, no successful receipt, or no amount.

    Amount and asset come from what the caller signed; network and transaction from the target's receipt.
    """
    payment = request.decoded_payment()
    receipt = _receipt(response)
    if payment is None or receipt is None or response.status_code >= 400 or receipt.get("success") is not True:
        return None

    accepted = payment.get("accepted") if isinstance(payment.get("accepted"), dict) else {}
    inner = payment.get("payload") if isinstance(payment.get("payload"), dict) else {}
    authorization = inner.get("authorization") if isinstance(inner.get("authorization"), dict) else {}
    amount = accepted.get("amount", authorization.get("value"))
    network = receipt.get("network") or accepted.get("network") or payment.get("network")
    transaction = receipt.get("transaction")
    asset = accepted.get("asset")
    if not (isinstance(amount, str) and amount.isascii() and amount.isdigit()):
        return None
    if not (isinstance(network, str) and isinstance(transaction, str) and transaction):
        return None
    if asset is not None and not isinstance(asset, str):
        return None

    return SettledPayment(
        host=urlsplit(request.url).hostname or "",
        network=network,
        asset=asset,
        amount=amount,
        transaction=transaction,
        settled_at=datetime.now(UTC),
    )


def _decode_json(value: str) -> dict[str, Any] | None:
    try:
        decoded = json.loads(base64.b64decode(value))
    except (binascii.Error, ValueError):
        return None
    return decoded if isinstance(decoded, dict) else None
