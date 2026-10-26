from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.ledger.models import PaymentsOverview

MAX_SITES = 100
MAX_RECENT = 25


class PaymentsReport:
    def __init__(self, ledger: PaymentLedger) -> None:
        self._ledger = ledger

    async def overview(self) -> PaymentsOverview:
        """What the public payments page shows."""
        return PaymentsOverview(
            sites=await self._ledger.site_totals(MAX_SITES), recent=await self._ledger.recent(MAX_RECENT)
        )
