from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from swarmpot.config import get_settings
from swarmpot.ledger.dependencies import get_payment_ledger
from swarmpot.ledger.interfaces import PaymentLedger
from swarmpot.proxy.application import ProxyService
from swarmpot.proxy.implementations import HttpxRequestForwarder
from swarmpot.proxy.interfaces import RequestForwarder


@lru_cache
def get_request_forwarder() -> RequestForwarder:
    settings = get_settings()
    return HttpxRequestForwarder(
        timeout_seconds=settings.proxy_timeout_seconds,
        max_response_bytes=settings.proxy_max_response_bytes,
        allow_private_targets=settings.proxy_allow_private_targets,
    )


def get_proxy_service(
    forwarder: Annotated[RequestForwarder, Depends(get_request_forwarder)],
    ledger: Annotated[PaymentLedger, Depends(get_payment_ledger)],
) -> ProxyService:
    return ProxyService(forwarder, ledger)
