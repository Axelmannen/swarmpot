from pydantic import BaseModel


class TargetResponse(BaseModel):
    """What the target answered. Header names are lowercase."""

    status_code: int
    headers: dict[str, str]
    body: bytes
