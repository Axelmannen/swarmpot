from datetime import datetime

from pydantic import BaseModel, Field


class SiteTotals(BaseModel):
    """Everything one site has been paid through the proxy in one asset on one network."""

    host: str
    network: str
    asset: str | None
    payments: int
    total: str = Field(description="Sum of the amounts, in atomic units")
    last_settled_at: datetime
