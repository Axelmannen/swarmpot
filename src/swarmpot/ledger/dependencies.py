from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from swarmpot.config import get_settings
from swarmpot.ledger.application import PaymentsReport
from swarmpot.ledger.implementations import SqlitePaymentLedger
from swarmpot.ledger.interfaces import PaymentLedger


@lru_cache
def get_payment_ledger() -> PaymentLedger:
    return SqlitePaymentLedger(get_settings().ledger_path)


def get_payments_report(ledger: Annotated[PaymentLedger, Depends(get_payment_ledger)]) -> PaymentsReport:
    return PaymentsReport(ledger)
