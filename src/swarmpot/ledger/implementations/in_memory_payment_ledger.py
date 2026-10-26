from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.ledger.models import SettledPayment, SiteTotals


class InMemoryPaymentLedger(PaymentLedger):
    """Keeps payments in a dict, lost on restart. For tests."""

    def __init__(self) -> None:
        self.payments: dict[str, SettledPayment] = {}

    async def record(self, payment: SettledPayment) -> None:
        self.payments.setdefault(payment.transaction, payment)

    async def site_totals(self, limit: int) -> list[SiteTotals]:
        totals: dict[tuple[str, str, str | None], SiteTotals] = {}
        for p in sorted(self.payments.values(), key=lambda p: p.settled_at):
            key = (p.host, p.network, p.asset)
            current = totals.get(key)
            totals[key] = SiteTotals(
                host=p.host,
                network=p.network,
                asset=p.asset,
                payments=(current.payments if current else 0) + 1,
                total=str((int(current.total) if current else 0) + int(p.amount)),
                last_settled_at=p.settled_at,
            )
        return sorted(totals.values(), key=lambda t: (-t.payments, t.host))[:limit]

    async def recent(self, limit: int) -> list[SettledPayment]:
        return sorted(self.payments.values(), key=lambda p: p.settled_at, reverse=True)[:limit]
