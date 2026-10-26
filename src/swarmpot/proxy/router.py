from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from swarmpot.proxy.application import ProxyService
from swarmpot.proxy.dependencies import get_proxy_service
from swarmpot.proxy.models import ProxyRequest, TargetBlocked, TargetUnreachable

router = APIRouter(prefix="/api/proxy", tags=["proxy"])

Service = Annotated[ProxyService, Depends(get_proxy_service)]


@router.get(
    "",
    response_class=Response,
    responses={
        200: {"description": "The target's response, passed through (with its PAYMENT-RESPONSE header when paid)"},
        402: {"description": "The target rejected the payment; its PAYMENT-REQUIRED header says why"},
        403: {"description": "The target is not a public address"},
        502: {"description": "The target could not be reached, timed out or answered with too large a body"},
    },
)
async def proxy(request: Annotated[ProxyRequest, Query()], service: Service) -> Response:
    """Forward a request to another site, optionally with a pre-signed x402 payment, and return its response."""
    try:
        target = await service.forward(request)
    except TargetBlocked as e:
        raise HTTPException(status_code=403, detail=str(e))
    except TargetUnreachable as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=target.body, status_code=target.status_code, headers=target.headers)
