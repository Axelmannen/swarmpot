import base64
import json
from typing import Any


def signed_payment(version: int = 2, **extra: Any) -> str:
    """A base64 payload shaped like an x402 payment. The proxy only reads its version; the target verifies it."""
    payload = {"x402Version": version, "payload": {"signature": "0xsig"}, **extra}
    return base64.b64encode(json.dumps(payload).encode()).decode()


def b64url(value: str | bytes | dict[str, str]) -> str:
    raw = json.dumps(value).encode() if isinstance(value, dict) else value
    raw = raw.encode() if isinstance(raw, str) else raw
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def receipt(success: bool = True, transaction: str = "0xabc", network: str = "eip155:84532") -> str:
    """A base64 settlement receipt, as a target puts in PAYMENT-RESPONSE."""
    settled = {"success": success, "transaction": transaction, "network": network, "payer": "0xpayer"}
    return base64.b64encode(json.dumps(settled).encode()).decode()
