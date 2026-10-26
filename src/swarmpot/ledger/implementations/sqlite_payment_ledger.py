import asyncio
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.ledger.models import SettledPayment, SiteTotals

# Amounts are TEXT: atomic units of 18-decimal tokens overflow SQLite's 64-bit integers, so totals are
# summed in Python. An unknown asset is stored as '' so it can be part of the totals' primary key.
SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    tx         TEXT PRIMARY KEY,
    host       TEXT NOT NULL,
    network    TEXT NOT NULL,
    asset      TEXT NOT NULL,
    amount     TEXT NOT NULL,
    settled_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS payments_settled_at ON payments (settled_at);
CREATE TABLE IF NOT EXISTS site_totals (
    host            TEXT NOT NULL,
    network         TEXT NOT NULL,
    asset           TEXT NOT NULL,
    payments        INTEGER NOT NULL,
    total           TEXT NOT NULL,
    last_settled_at TEXT NOT NULL,
    PRIMARY KEY (host, network, asset)
);
"""


class SqlitePaymentLedger(PaymentLedger):
    """Keeps payments in a SQLite file. Queries run one at a time in a worker thread."""

    def __init__(self, path: Path | str) -> None:
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._db.executescript(SCHEMA)

    async def record(self, payment: SettledPayment) -> None:
        await asyncio.to_thread(self._record, payment)

    async def site_totals(self, limit: int) -> list[SiteTotals]:
        rows = await asyncio.to_thread(
            self._query, "SELECT * FROM site_totals ORDER BY payments DESC, host LIMIT ?", limit
        )
        return [
            SiteTotals(
                host=r["host"],
                network=r["network"],
                asset=r["asset"] or None,
                payments=r["payments"],
                total=r["total"],
                last_settled_at=datetime.fromisoformat(r["last_settled_at"]),
            )
            for r in rows
        ]

    async def recent(self, limit: int) -> list[SettledPayment]:
        rows = await asyncio.to_thread(self._query, "SELECT * FROM payments ORDER BY settled_at DESC LIMIT ?", limit)
        return [
            SettledPayment(
                host=r["host"],
                network=r["network"],
                asset=r["asset"] or None,
                amount=r["amount"],
                transaction=r["tx"],
                settled_at=datetime.fromisoformat(r["settled_at"]),
            )
            for r in rows
        ]

    def _record(self, p: SettledPayment) -> None:
        key = (p.host, p.network, p.asset or "")
        settled_at = p.settled_at.isoformat()
        with self._lock, self._db:
            inserted = self._db.execute(
                "INSERT OR IGNORE INTO payments VALUES (?, ?, ?, ?, ?, ?)", (p.transaction, *key, p.amount, settled_at)
            ).rowcount
            if not inserted:
                return
            row = self._db.execute(
                "SELECT payments, total FROM site_totals WHERE host = ? AND network = ? AND asset = ?", key
            ).fetchone()
            payments, total = (row["payments"], int(row["total"])) if row else (0, 0)
            self._db.execute(
                "INSERT OR REPLACE INTO site_totals VALUES (?, ?, ?, ?, ?, ?)",
                (*key, payments + 1, str(total + int(p.amount)), settled_at),
            )

    def _query(self, sql: str, *params: object) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(sql, params).fetchall()
