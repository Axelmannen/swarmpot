"""A real x402 target (the SDK's FastAPI middleware) paid through the proxy. Uses the public facilitator."""

import socket
import threading
import time
from collections.abc import Iterator

import httpx
import pytest
import uvicorn
from eth_account import Account
from fastapi import FastAPI
from fastapi.testclient import TestClient
from x402 import x402Client
from x402.http import HTTPFacilitatorClient
from x402.http.middleware.fastapi import payment_middleware_from_config
from x402.http.types import PaymentOption, RouteConfig
from x402.http.utils import decode_payment_required_header, encode_payment_signature_header
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact import ExactEvmClientScheme, ExactEvmServerScheme

from swarmpot.ledger.dependencies import get_payment_ledger
from swarmpot.ledger.implementations import InMemoryPaymentLedger
from swarmpot.main import app
from swarmpot.proxy.dependencies import get_request_forwarder
from swarmpot.proxy.implementations import HttpxRequestForwarder

from .payments import b64url

pytestmark = [pytest.mark.anyio, pytest.mark.facilitator]

NETWORK = "eip155:84532"  # Base Sepolia


def paid_target() -> FastAPI:
    target = FastAPI()
    routes = {
        "POST /generate": RouteConfig(
            accepts=PaymentOption(scheme="exact", pay_to=Account.create().address, price="$0.01", network=NETWORK),
        )
    }
    target.middleware("http")(
        payment_middleware_from_config(
            routes,
            facilitator_client=HTTPFacilitatorClient({"url": "https://x402.org/facilitator"}),
            schemes=[{"network": NETWORK, "server": ExactEvmServerScheme()}],
        )
    )

    @target.post("/generate")
    def generate() -> dict[str, str]:
        return {"text": "paid content"}

    return target


@pytest.fixture(scope="module")
def target_url() -> Iterator[str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(paid_target(), host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/generate"
    server.should_exit = True


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_request_forwarder] = lambda: HttpxRequestForwarder(
        timeout_seconds=30, max_response_bytes=1_000_000, allow_private_targets=True
    )
    app.dependency_overrides[get_payment_ledger] = InMemoryPaymentLedger
    yield TestClient(app)
    app.dependency_overrides.clear()


async def test_signed_payment_reaches_target_and_its_verdict_comes_back(target_url: str, client: TestClient) -> None:
    # 1. The client asks the target for its price, and signs locally (an empty wallet, so it cannot settle).
    challenge = httpx.post(target_url, json={"prompt": "hi"})
    assert challenge.status_code == 402
    signer = x402Client().register(NETWORK, ExactEvmClientScheme(signer=EthAccountSigner(Account.create())))
    payload = await signer.create_payment_payload(decode_payment_required_header(challenge.headers["PAYMENT-REQUIRED"]))
    payment = encode_payment_signature_header(payload)

    # 2. One GET to the proxy, with the payment url-safe and unpadded as a query string would carry it.
    response = client.get(
        "/api/proxy",
        params={
            "url": target_url,
            "payment": payment.replace("+", "-").replace("/", "_").rstrip("="),
            "method": "POST",
            "body": b64url('{"prompt":"hi"}'),
            "headers": b64url({"Content-Type": "application/json"}),
        },
    )

    # 3. The target verified the payment with the facilitator, which found the wallet empty.
    assert response.status_code == 402
    assert decode_payment_required_header(response.headers["PAYMENT-REQUIRED"]).error == (
        "invalid_exact_evm_insufficient_balance"
    )
