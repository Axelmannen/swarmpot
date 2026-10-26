from pydantic import BaseModel


class OutboundRequest(BaseModel):
    """The request the proxy sends to the target, payment header included."""

    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None = None
