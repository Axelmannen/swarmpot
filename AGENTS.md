# AGENTS.md

Guide for agents (and humans) working in this codebase. Read this before adding or moving code.

## What this is

swarmpot is a relay for [x402](https://www.x402.org) payments. A client signs an x402 payment for some other site, puts it in a URL, and calls `GET /api/proxy`. swarmpot rebuilds the real request, attaches the payment and returns the site's response. It never verifies, settles or holds funds: the site does that, and the signature can only pay the site's `payTo`. When a site reports a settled payment, swarmpot records it for the public payments page at `/payments/`.

## Stack

- Python 3.13, managed with **uv** (`uv add`, `uv run` — never `pip install`)
- **FastAPI** for HTTP, **httpx** for calls to target sites
- **Svelte 5 + Vite + TypeScript** frontend in `frontend/`: explains swarmpot and builds proxy URLs. No wallet code; signing happens in the user's own client.
- The `x402` Python SDK is a **dev** dependency only: tests use it to run a real x402 target and sign real payments. The proxy itself never imports it.

## Layout

The app is split into **modules** by feature. Every module uses the same four layer folders, plus a router and the wiring that connects them. A module leaves out folders it has no use for.

```
src/swarmpot/
  main.py                    # creates the FastAPI app, includes routers, serves frontend/dist
  config.py                  # Settings, read from SWARMPOT_* env vars / .env
  redact_payment_filter.py   # keeps `payment=` query params out of the access log
  proxy/                     # GET /api/proxy
  ledger/                    # settled payments, GET /api/payments
  <module>/
    models/                  # domain types
    interfaces/              # abstract contracts
    implementations/         # concrete classes that fulfil the interfaces
    application/             # use cases: what the module does
    router.py                # HTTP endpoints
    dependencies.py          # wiring: picks which implementation backs each interface
tests/
  <module>/                  # mirrors src/swarmpot/<module>/
frontend/                    # Svelte app (see "Frontend" below)
```

## The layers

### `models/` — what things are
Pydantic models for the module's domain (`OutboundRequest`, `TargetResponse`), the request/response bodies its router uses (`ProxyRequest`), and domain exceptions (`TargetBlocked`, `TargetUnreachable`). Plain data plus validation and small pure methods. **No I/O, no imports from other layers.**

### `interfaces/` — what we need
Abstract base classes (`abc.ABC` + `@abstractmethod`) describing a capability, named after the role, not the technology:

```python
# proxy/interfaces/request_forwarder.py
class RequestForwarder(ABC):
    @abstractmethod
    async def send(self, request: OutboundRequest) -> TargetResponse:
        """Raises TargetBlocked for non-public targets, TargetUnreachable when they can't be reached."""
```

Interfaces take and return `models`. They never mention HTTP clients, SQL, or library types.

### `implementations/` — how we do it
Concrete subclasses of an interface, named after the technology plus the role:

```
proxy/implementations/httpx_request_forwarder.py   # class HttpxRequestForwarder(RequestForwarder)
proxy/implementations/fake_request_forwarder.py    # class FakeRequestForwarder(RequestForwarder)
```

This is the only layer allowed to import third-party I/O libraries (httpx, database drivers). Every interface should have an in-memory or fake implementation for tests and local dev.

### `application/` — what the module does
The use cases. Classes that receive **interfaces** in their constructor and orchestrate them:

```python
# proxy/application/proxy_service.py
class ProxyService:
    def __init__(self, forwarder: RequestForwarder) -> None: ...

    async def forward(self, request: ProxyRequest) -> TargetResponse: ...
```

Business rules live here (which header carries the payment, which response headers go back). Application code never imports from `implementations/` and never touches FastAPI (`Request`, `HTTPException`, `Depends`). Raise domain exceptions; the router translates them to HTTP.

### `router.py` — HTTP
Thin FastAPI endpoints: parse the request, call one application method, map the result/exceptions to a response. No business logic.

### `dependencies.py` — wiring
The **only** file that imports `implementations/`. It builds them (from `config`) and exposes `Depends()` providers that construct the application classes:

```python
def get_proxy_service(forwarder: Annotated[RequestForwarder, Depends(get_request_forwarder)]) -> ProxyService:
    return ProxyService(forwarder)
```

Long-lived implementations are module-level singletons via `@lru_cache`.

Tests swap implementations with `app.dependency_overrides`.

## Import rules

Dependencies point inward. Allowed imports:

| From              | May import                                  |
|-------------------|---------------------------------------------|
| `models`          | nothing in the project (stdlib + pydantic)  |
| `interfaces`      | `models`                                    |
| `implementations` | `interfaces`, `models`, `config`            |
| `application`     | `interfaces`, `models`                      |
| `router`          | `application`, `models`, `dependencies`     |
| `dependencies`    | everything in its module, `config`          |

Across modules: import another module's `models`, `interfaces` or `application` — **never its `implementations`** — and reuse its `dependencies` providers.

## The proxy

`GET /api/proxy` forwards any request (method, body, a few headers) described in its query string. To pay, the client gets the target's 402 itself, signs locally, and adds the signed payload as `payment`:

| Param     | Required | Contents |
|-----------|----------|----------|
| `url`     | yes      | Target URL |
| `payment` | no       | Leave out for a plain request. Otherwise a signed x402 payload, base64 or base64url, padding optional. Its `x402Version` picks the header: v2 → `PAYMENT-SIGNATURE`, v1 → `X-PAYMENT`. Always forwarded as standard base64 |
| `method`  | no       | `GET` (default), `POST`, `PUT`, `PATCH`, `DELETE` |
| `body`    | no       | Request body, base64url |
| `headers` | no       | base64url JSON object; only `Accept`, `Accept-Language`, `Authorization`, `Content-Type`, `User-Agent` |
| `receipt` | no       | `header` (default) or `body`. `body` answers 200 with JSON `{status, content_type, receipt, payment_required, body, body_encoding}` (`WrappedResponse`), for clients such as agent fetch tools that can't read headers or non-2xx bodies |

Responses (default `receipt=header`): the target's status and body, with `Content-Type`, `Location`, `Retry-After` and the x402 headers (`PAYMENT-REQUIRED`, `PAYMENT-RESPONSE`, `X-PAYMENT-RESPONSE`) passed through, plus `Cache-Control: no-store` and `Referrer-Policy: no-referrer`. `422` for a malformed request, `403` for a target that resolves to a non-public address, `502` when the target is unreachable, slow or too large.

Security rules to keep:

- The payment in the query string is spendable until it settles. Never log it (`RedactPaymentFilter` handles uvicorn's access log).
- `HttpxRequestForwarder` resolves the target once, rejects non-public addresses, and connects to the address it checked (original `Host` and TLS name kept), so DNS rebinding can't reach internal hosts. Redirects are returned, not followed.
- The header allowlist lives in `ProxyRequest` (`ALLOWED_HEADERS`) and is mirrored in `frontend/src/lib/proxy.ts`.

### The payments ledger

`ProxyService` records a payment in the `ledger` module's `PaymentLedger` when the target answers below 400 with a receipt (`PAYMENT-RESPONSE` or `X-PAYMENT-RESPONSE`) that says `success: true` and names a transaction. Amount and asset come from the signed payment, network and transaction from the receipt. `GET /api/payments` returns totals per site and the 25 latest payments; the frontend shows them at `/payments/`.

- Only the target's host is stored, never its path or query. The payer's wallet is not stored either, though a transaction hash leads to it on-chain.
- A transaction is recorded once, so a replayed receipt doesn't inflate totals.
- Receipts are the site's word: nothing checks them on-chain, so a site can report fake payments. The page links each transaction to a block explorer so readers can check.
- Amounts are atomic units kept as strings (18-decimal tokens overflow SQLite integers).

### Configuration

| Env var                                | Default    | Meaning |
|----------------------------------------|------------|---------|
| `SWARMPOT_PROXY_TIMEOUT_SECONDS`       | `30`       | How long the proxy waits for a target |
| `SWARMPOT_PROXY_MAX_RESPONSE_BYTES`    | `10000000` | Largest target response the proxy passes back |
| `SWARMPOT_PROXY_ALLOW_PRIVATE_TARGETS` | `false`    | Let the proxy reach localhost/private networks. Local dev only (SSRF) |
| `SWARMPOT_LEDGER_PATH`                 | `swarmpot.sqlite3` | SQLite file for the payments ledger |

Put them in `.env` (see `.env.example`).

## Frontend

```
frontend/src/
  App.svelte                 # the explainer page (/), composition only
  Payments.svelte            # the public payments page (/payments/, entry payments/index.html), composition only
  app.css                    # design tokens (white, Inter, thin borders, soft shadows, accent colors), shared .btn/.card/.tinted
  lib/
    proxy.ts                 # builds proxy URLs and calls /api/proxy; mirrors the backend's params
    payment.ts               # decodes a pasted x402 payment to show what it pays
    ledger.ts                # fetches /api/payments; mirrors swarmpot.ledger.models
    base64.ts                # base64/base64url helpers
    format.ts                # pure formatting helpers (amounts, networks, expiry)
    examples.ts              # client code shown on the page
    components/              # one component per file, PascalCase, scoped <style>
```

- Svelte 5 runes only (`$state`, `$derived`, `$props`), no stores or `export let`.
- Components get data through props and report back through callback props (`onsend`); only the page components (`App.svelte`, `Payments.svelte`) and `lib/*.ts` call the API.
- Use the CSS tokens from `app.css`; never hardcode colors in components.
- The code in `examples.ts` is run against a real x402 server (see `tests/proxy/test_end_to_end.py` for one) before it changes.
- In dev, Vite proxies `/api` to FastAPI on :8765. In production FastAPI serves `frontend/dist` from the same origin.

## Conventions

- One class per file; the file is named after the class in snake_case.
- Each layer folder has an `__init__.py` that re-exports its public names, so imports read `from swarmpot.proxy.models import ProxyRequest`.
- Async all the way down for anything doing I/O.
- Type hints everywhere; Pydantic for anything crossing a boundary.
- Tests: application tests use fake implementations directly (no FastAPI); router tests use `TestClient` + `dependency_overrides`; implementation tests hit the real thing. Tests that need the internet are marked `@pytest.mark.network`, or `@pytest.mark.facilitator` when they use the public x402 facilitator, so they can be skipped. Async tests use `pytest.mark.anyio`.

## Commands

```sh
uv sync                              # install backend
uv run fastapi dev --port 8765       # API with reload on :8765 (docs at /docs)
uv run pytest                        # all tests (includes live facilitator and network tests)
uv run pytest -m "not facilitator and not network"   # offline tests only
uv add <pkg>                         # add a backend dependency

cd frontend
npm install
npm run dev                          # Vite on :5173, proxies /api to :8765
npm run check                        # svelte-check + tsc
npm run build                        # build to frontend/dist, served by FastAPI
```

## Adding a new module

1. Create `src/swarmpot/<module>/` with `models/`, `interfaces/`, `implementations/`, `application/`, `router.py`, `dependencies.py`.
2. Write models → interfaces → a fake implementation → application → router, in that order.
3. Include the router in `main.py`.
4. Mirror it in `tests/<module>/`.
