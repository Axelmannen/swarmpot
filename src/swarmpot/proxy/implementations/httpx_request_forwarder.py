import asyncio
import ipaddress
import socket

import httpx

from swarmpot.proxy.interfaces import RequestForwarder
from swarmpot.proxy.models import OutboundRequest, TargetBlocked, TargetResponse, TargetUnreachable

type IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


class HttpxRequestForwarder(RequestForwarder):
    """Sends requests with httpx, refusing targets that resolve to non-public addresses.

    The host is resolved once, every address is checked, and the connection goes to the checked
    address (with the original Host header and TLS server name), so a DNS answer that changes
    between the check and the connect cannot redirect the request into a private network.
    """

    def __init__(self, timeout_seconds: float, max_response_bytes: int, allow_private_targets: bool = False) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_response_bytes = max_response_bytes
        self._allow_private_targets = allow_private_targets

    async def send(self, request: OutboundRequest) -> TargetResponse:
        url = httpx.URL(request.url)
        host = url.raw_host.decode("ascii")
        address = await self._resolve(host, url.port or (443 if url.scheme == "https" else 80))
        extensions = {"sni_hostname": host} if url.scheme == "https" else {}

        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
                async with client.stream(
                    request.method,
                    url.copy_with(host=str(address)),
                    headers={**request.headers, "Host": url.netloc.decode("ascii")},
                    content=request.body,
                    extensions=extensions,
                ) as response:
                    body = await self._read_body(response)
        except httpx.TimeoutException:
            raise TargetUnreachable(f"{host} timed out") from None
        except httpx.HTTPError as e:
            raise TargetUnreachable(f"{host}: {e}") from None

        return TargetResponse(status_code=response.status_code, headers=dict(response.headers), body=body)

    async def _resolve(self, host: str, port: int) -> IPAddress:
        try:
            infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror:
            raise TargetUnreachable(f"could not resolve {host}") from None
        addresses = [ipaddress.ip_address(info[4][0]) for info in infos]
        if not self._allow_private_targets:
            blocked = [a for a in addresses if not _is_public(a)]
            if blocked:
                raise TargetBlocked(f"{host} resolves to a non-public address ({blocked[0]})")
        # Prefer IPv4: plenty of hosts publish AAAA records that this machine cannot route to.
        return min(addresses, key=lambda a: a.version)

    async def _read_body(self, response: httpx.Response) -> bytes:
        body = bytearray()
        async for chunk in response.aiter_bytes():
            body += chunk
            if len(body) > self._max_response_bytes:
                raise TargetUnreachable(f"response is larger than {self._max_response_bytes} bytes")
        return bytes(body)


def _is_public(address: IPAddress) -> bool:
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast
