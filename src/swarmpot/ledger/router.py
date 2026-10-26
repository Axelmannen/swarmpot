from typing import Annotated

from fastapi import APIRouter, Depends

from swarmpot.ledger.application import PaymentsReport
from swarmpot.ledger.dependencies import get_payments_report
from swarmpot.ledger.models import PaymentsOverview

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("")
async def payments(report: Annotated[PaymentsReport, Depends(get_payments_report)]) -> PaymentsOverview:
    """Payments settled through the proxy, as the paid sites reported them: totals per site and the latest ones."""
    return await report.overview()
