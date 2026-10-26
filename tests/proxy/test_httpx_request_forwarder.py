import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from swarmpot.proxy.implementations import HttpxRequestForwarder
from swarmpot.proxy.models import OutboundRequest, TargetBlocked, TargetUnreachable

pytestmark = pytest.mark.anyio


class EchoHandler(BaseHTTPRequestHandler):
    """Answers 402 with the request it received, as JSON."""

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        echo = {"method": self.command, "path": self.path, "headers": dict(self.headers), "body": body.decode()}
        self.send_response(402)
        self.send_header("Content-Type", "application/json")
        self.send_header("PAYMENT-REQUIRED", "requirements")
        self.end_headers()
        self.wfile.write(json.dumps(echo).encode())

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def local_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), EchoHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://localhost:{server.server_port}"
    server.shutdown()


async def test_request_reaches_target_with_original_host(local_server: str) -> None:
    forwarder = HttpxRequestForwarder(timeout_seconds=5, max_response_bytes=10_000, allow_private_targets=True)

    response = await forwarder.send(
        OutboundRequest(
            method="POST",
            url=f"{local_server}/generate?x=1",
            headers={"PAYMENT-SIGNATURE": "signed", "Content-Type": "application/json"},
            body=b'{"prompt":"hi"}',
        )
    )

    echo = json.loads(response.body)
    assert response.status_code == 402
    assert response.headers["payment-required"] == "requirements"
    assert echo["path"] == "/generate?x=1"
    assert echo["body"] == '{"prompt":"hi"}'
    assert echo["headers"]["Host"] == local_server.removeprefix("http://")
    assert echo["headers"]["PAYMENT-SIGNATURE"] == "signed"


async def test_oversized_response_is_refused(local_server: str) -> None:
    forwarder = HttpxRequestForwarder(timeout_seconds=5, max_response_bytes=10, allow_private_targets=True)

    with pytest.raises(TargetUnreachable, match="larger than"):
        await forwarder.send(OutboundRequest(method="POST", url=local_server, headers={}))


@pytest.mark.parametrize(
    "url",
    ["http://localhost:8000/", "http://127.0.0.1/", "http://10.0.0.1/", "http://169.254.169.254/latest/meta-data", "http://[::ffff:127.0.0.1]/"],
)
async def test_non_public_targets_are_blocked(url: str) -> None:
    forwarder = HttpxRequestForwarder(timeout_seconds=5, max_response_bytes=10_000)

    with pytest.raises(TargetBlocked):
        await forwarder.send(OutboundRequest(method="GET", url=url, headers={}))


async def test_unresolvable_host_is_unreachable() -> None:
    forwarder = HttpxRequestForwarder(timeout_seconds=5, max_response_bytes=10_000)

    with pytest.raises(TargetUnreachable, match="could not resolve"):
        await forwarder.send(OutboundRequest(method="GET", url="http://does-not-exist.invalid/", headers={}))


@pytest.mark.network
async def test_https_target_verifies_tls_against_the_original_hostname() -> None:
    forwarder = HttpxRequestForwarder(timeout_seconds=15, max_response_bytes=1_000_000)

    response = await forwarder.send(
        OutboundRequest(method="GET", url="https://x402.org/facilitator/supported", headers={})
    )

    assert response.status_code == 200
    assert "kinds" in json.loads(response.body)
