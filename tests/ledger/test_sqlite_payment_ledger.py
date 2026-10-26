from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from swarmpot.ledger.implementations import InMemoryPaymentLedger, SqlitePaymentLedger
from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.ledger.models import SettledPayment

pytestmark = pytest.mark.anyio

START = datetime(2026, 10, 1, tzinfo=UTC)


def payment(
    tx: str, host: str = "api.example.com", amount: str = "10000", minutes: int = 0, **extra: str | None
) -> SettledPayment:
    fields = {"network": "eip155:8453", "asset": "0xUSDC"} | extra
    return SettledPayment(
        host=host, amount=amount, transaction=tx, settled_at=START + timedelta(minutes=minutes), **fields
    )


@pytest.fixture(params=["sqlite", "memory"])
def ledger(request: pytest.FixtureRequest, tmp_path: Path) -> PaymentLedger:
    return SqlitePaymentLedger(tmp_path / "ledger.sqlite3") if request.param == "sqlite" else InMemoryPaymentLedger()


async def test_totals_are_per_site_busiest_first(ledger: PaymentLedger) -> None:
    await ledger.record(payment("0x1", host="a.example", minutes=1))
    await ledger.record(payment("0x2", host="b.example", minutes=2))
    await ledger.record(payment("0x3", host="b.example", amount="5", minutes=3))

    totals = await ledger.site_totals(10)

    assert [(t.host, t.payments, t.total, t.last_settled_at.minute) for t in totals] == [
        ("b.example", 2, "10005", 3),
        ("a.example", 1, "10000", 1),
    ]


async def test_same_transaction_counts_once(ledger: PaymentLedger) -> None:
    await ledger.record(payment("0x1"))
    await ledger.record(payment("0x1", minutes=5))

    [totals] = await ledger.site_totals(10)
    assert totals.payments == 1
    assert len(await ledger.recent(10)) == 1


async def test_large_amounts_do_not_overflow(ledger: PaymentLedger) -> None:
    huge = str(10**30)
    await ledger.record(payment("0x1", amount=huge))
    await ledger.record(payment("0x2", amount=huge))

    [totals] = await ledger.site_totals(10)
    assert totals.total == str(2 * 10**30)


async def test_unknown_asset_is_kept_apart(ledger: PaymentLedger) -> None:
    await ledger.record(payment("0x1"))
    await ledger.record(payment("0x2", asset=None, network="base"))

    assert sorted(str(t.asset) for t in await ledger.site_totals(10)) == ["0xUSDC", "None"]
    assert {p.asset for p in await ledger.recent(10)} == {"0xUSDC", None}


async def test_recent_is_newest_first_and_limited(ledger: PaymentLedger) -> None:
    for i in range(5):
        await ledger.record(payment(f"0x{i}", minutes=i))

    assert [p.transaction for p in await ledger.recent(3)] == ["0x4", "0x3", "0x2"]


async def test_sqlite_ledger_survives_reopening(tmp_path: Path) -> None:
    await SqlitePaymentLedger(tmp_path / "ledger.sqlite3").record(payment("0x1"))

    [kept] = await SqlitePaymentLedger(tmp_path / "ledger.sqlite3").recent(10)

    assert kept == payment("0x1")
