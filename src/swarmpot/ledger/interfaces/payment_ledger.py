from abc import ABC, abstractmethod

from swarmpot.ledger.models import SettledPayment, SiteTotals


class PaymentLedger(ABC):
    @abstractmethod
    async def record(self, payment: SettledPayment) -> None:
        """Adds a payment. A transaction that is already recorded is ignored, so a replayed receipt counts once."""

    @abstractmethod
    async def site_totals(self, limit: int) -> list[SiteTotals]:
        """Totals per (host, network, asset), most payments first."""

    @abstractmethod
    async def recent(self, limit: int) -> list[SettledPayment]:
        """The latest payments, newest first."""
