from pydantic import BaseModel

from .settled_payment import SettledPayment
from .site_totals import SiteTotals


class PaymentsOverview(BaseModel):
    """The public view of the ledger: totals per site, busiest first, and the latest payments."""

    sites: list[SiteTotals]
    recent: list[SettledPayment]
