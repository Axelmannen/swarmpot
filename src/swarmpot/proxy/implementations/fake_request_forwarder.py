from swarmpot.proxy.interfaces import RequestForwarder
from swarmpot.proxy.models import OutboundRequest, TargetResponse


class FakeRequestForwarder(RequestForwarder):
    """Records what it is asked to send and answers with a canned response, or raises `error`. For tests."""

    def __init__(self, response: TargetResponse | None = None, error: Exception | None = None) -> None:
        self.response = response or TargetResponse(
            status_code=200, headers={"content-type": "text/plain"}, body=b"paid content"
        )
        self.error = error
        self.sent: list[OutboundRequest] = []

    async def send(self, request: OutboundRequest) -> TargetResponse:
        self.sent.append(request)
        if self.error:
            raise self.error
        return self.response
