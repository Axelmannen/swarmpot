from abc import ABC, abstractmethod

from swarmpot.proxy.models import OutboundRequest, TargetResponse


class RequestForwarder(ABC):
    @abstractmethod
    async def send(self, request: OutboundRequest) -> TargetResponse:
        """Send `request` to its target and return the response, without following redirects.

        Raises TargetBlocked when the target is not a public address, and TargetUnreachable when it
        cannot be reached, times out or answers with too large a body.
        """
