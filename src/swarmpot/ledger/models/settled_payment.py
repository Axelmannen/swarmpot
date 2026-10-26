from datetime import datetime

from pydantic import BaseModel, Field


class SettledPayment(BaseModel):
    """A payment a site settled for a request sent through the proxy. Only the site's host is kept, never the path."""

    host: str
    network: str
    asset: str | None = Field(description="Token contract, when the payment names one")
    amount: str = Field(pattern=r"^[0-9]+$", description="Atomic units of the asset")
    transaction: str = Field(description="Settlement transaction hash, as the site reported it")
    settled_at: datetime
