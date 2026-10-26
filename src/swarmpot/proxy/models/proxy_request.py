import base64
import binascii
import json
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

# Headers a caller may pass through to the target. Everything else (Host, Cookie, hop-by-hop,
# the payment headers themselves) is rejected rather than silently dropped.
ALLOWED_HEADERS = frozenset({"accept", "accept-language", "authorization", "content-type", "user-agent"})


class ProxyRequest(BaseModel):
    """A request for the proxy to forward, as given in the query string of GET /api/proxy. The payment is optional."""

    url: str = Field(max_length=2048, description="Target URL, including its own query string")
    payment: str | None = Field(
        None,
        max_length=8192,
        description="Signed x402 payment payload (base64 or base64url), as it would go in PAYMENT-SIGNATURE. "
        "Leave out to forward the request without paying.",
    )
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    body: str | None = Field(None, max_length=8192, description="Request body, base64url")
    headers: str | None = Field(
        None,
        max_length=4096,
        description=f"Extra headers as a base64url JSON object. Allowed: {', '.join(sorted(ALLOWED_HEADERS))}",
    )
    receipt: Literal["header", "body"] = Field(
        "header",
        description="body: answer 200 with JSON holding the target's status, decoded receipt and body, "
        "for clients that can't read response headers",
    )

    @field_validator("url")
    @classmethod
    def _check_url(cls, url: str) -> str:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("must be an absolute http(s) URL")
        return url

    @field_validator("payment")
    @classmethod
    def _check_payment(cls, payment: str | None) -> str | None:
        if payment is not None:
            _decode_payment(payment)
        return payment

    @field_validator("body")
    @classmethod
    def _check_body(cls, body: str | None) -> str | None:
        if body is not None:
            _decode(body)
        return body

    @field_validator("headers")
    @classmethod
    def _check_headers(cls, headers: str | None) -> str | None:
        if headers is not None:
            _decode_headers(headers)
        return headers

    def payment_version(self) -> int | None:
        """The x402 protocol version the payment was signed for (1 or 2), or None without a payment."""
        return None if self.payment is None else _decode_payment(self.payment)[0]

    def decoded_payment(self) -> dict[str, Any] | None:
        return None if self.payment is None else json.loads(_decode_payment(self.payment)[1])

    def payment_header_value(self) -> str | None:
        """The payment re-encoded as standard base64, which is what x402 servers decode."""
        return None if self.payment is None else base64.b64encode(_decode_payment(self.payment)[1]).decode()

    def decoded_body(self) -> bytes | None:
        return None if self.body is None else _decode(self.body)

    def decoded_headers(self) -> dict[str, str]:
        return {} if self.headers is None else _decode_headers(self.headers)


def _decode(value: str) -> bytes:
    """Decode standard or URL-safe base64, padded or not. A `+` that a query string turned into a space is restored."""
    normalized = value.strip().replace(" ", "+").replace("-", "+").replace("_", "/")
    try:
        return base64.b64decode(normalized + "=" * (-len(normalized) % 4), validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("is not valid base64") from None


def _decode_payment(payment: str) -> tuple[int, bytes]:
    raw = _decode(payment)
    try:
        payload: Any = json.loads(raw)
    except ValueError:
        raise ValueError("is not an x402 payment payload (expected base64 JSON)") from None
    if not isinstance(payload, dict):
        raise ValueError("is not an x402 payment payload (expected a JSON object)")
    version = payload.get("x402Version", 2)  # the x402 SDKs treat a missing version as v2
    if version not in (1, 2):
        raise ValueError(f"has unsupported x402Version {version!r}")
    return version, raw


def _decode_headers(headers: str) -> dict[str, str]:
    try:
        parsed: Any = json.loads(_decode(headers))
    except ValueError as e:
        raise ValueError(f"must be base64url JSON: {e}") from None
    if not isinstance(parsed, dict) or not all(isinstance(v, str) for v in parsed.values()):
        raise ValueError("must be a JSON object of string values")
    disallowed = sorted(name for name in parsed if name.lower() not in ALLOWED_HEADERS)
    if disallowed:
        raise ValueError(f"may not set {', '.join(disallowed)}")
    return parsed
