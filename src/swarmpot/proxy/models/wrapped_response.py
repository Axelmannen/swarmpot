from typing import Any, Literal

from pydantic import BaseModel, Field


class WrappedResponse(BaseModel):
    """The target's response as one JSON document (receipt=body), for clients that can't read headers, such as an
    agent's fetch tool. Sent with status 200 so such clients show it whatever the target answered."""

    status: int = Field(description="The target's HTTP status")
    content_type: str | None
    receipt: dict[str, Any] | None = Field(description="Decoded PAYMENT-RESPONSE: the settlement receipt, when paid")
    payment_required: dict[str, Any] | None = Field(
        description="Decoded PAYMENT-REQUIRED: on a 402, what the target accepts and why it refused the payment"
    )
    body: str
    body_encoding: Literal["text", "base64"] = Field(description="base64 when the body is not UTF-8 text")
