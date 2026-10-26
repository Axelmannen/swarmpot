# swarmpot

Pay any [x402](https://www.x402.org/) API with a single GET.

x402 sites want a request with a signed payment in a header, often a POST with a JSON body. Plenty of clients can only open a URL: agents with just a fetch tool, webhooks, spreadsheets, shell one-liners. swarmpot bridges the gap. You sign the payment yourself, put it in a URL, and swarmpot makes the real request with your payment attached, then returns the site's response and receipt:

```
GET /api/proxy?url=https://api.example.com/generate&payment=<signed payload>&method=POST&body=<base64url>
```

- **No keys, no funds.** swarmpot never signs or settles anything. The signature can only pay the site it was signed for, and that site verifies and settles it.
- **Any request.** Leave out `payment` and it is a plain relay: any method, body and a few safe headers, sent through one GET.
- **Receipts for fetch tools.** If your client can't read response headers, add `receipt=body`: swarmpot answers 200 with JSON holding the site's status, the decoded receipt (with the transaction hash) or, on a 402, why the payment was refused, and the body.
- **Public payments page.** `/payments/` lists the sites paid through the proxy, with totals and settlement transactions linked to a block explorer.

## Getting started

Requires [uv](https://docs.astral.sh/uv/) and Node.

```sh
uv sync
cd frontend && npm install && npm run build && cd ..
uv run fastapi dev --port 8765   # site + API on http://127.0.0.1:8765 (API docs at /docs)
```

The site explains the flow, has a request builder, and shows client code for signing with the official x402 SDKs.

Frontend development with hot reload: keep `uv run fastapi dev --port 8765` running and, in `frontend/`, run `npm run dev` (http://localhost:5173, proxies `/api`).

```sh
uv run pytest                                        # includes live tests against the public facilitator and internet
uv run pytest -m "not facilitator and not network"   # offline only
```

## Configuration

Set these in the environment or in `.env` (see `.env.example`):

| Env var                                | Default            | Meaning |
|----------------------------------------|--------------------|---------|
| `SWARMPOT_PROXY_TIMEOUT_SECONDS`       | `30`               | How long the proxy waits for a site |
| `SWARMPOT_PROXY_MAX_RESPONSE_BYTES`    | `10000000`         | Largest response the proxy passes back |
| `SWARMPOT_PROXY_ALLOW_PRIVATE_TARGETS` | `false`            | Let the proxy reach localhost and private networks, for testing against a local x402 server. Never in production |
| `SWARMPOT_LEDGER_PATH`                 | `swarmpot.sqlite3` | SQLite file behind the payments page |

## Before running it in public

- Anyone with the URL can send requests through your server's IP. Private and internal addresses are blocked, but there is no rate limiting or authentication yet.
- The payments page trusts each site's receipt. Nothing checks transactions on-chain, so a site can list fake payments; the explorer links let readers verify them.
- Payments travel in the query string. swarmpot keeps them out of its access log and sends `Cache-Control: no-store` and `Referrer-Policy: no-referrer`, but anything else in front of it (a reverse proxy, a CDN) may log URLs.

## Codebase

The backend is organised into feature modules (`proxy`, `ledger`), each split into the same four layers:

| Layer              | Holds                                   | Example                    |
|--------------------|-----------------------------------------|----------------------------|
| `models/`          | domain types (Pydantic), no I/O         | `ProxyRequest`, `TargetResponse` |
| `interfaces/`      | abstract contracts (ABCs)               | `RequestForwarder`, `PaymentLedger` |
| `implementations/` | concrete classes behind the interfaces  | `HttpxRequestForwarder`, `SqlitePaymentLedger` |
| `application/`     | use cases, depend only on interfaces    | `ProxyService.forward()`   |

Each module also has a thin `router.py` (HTTP) and a `dependencies.py` that wires implementations into the application layer with FastAPI's `Depends()`. The frontend is Svelte 5 + Vite in `frontend/`, served by FastAPI from `frontend/dist`.

See [AGENTS.md](AGENTS.md) for every proxy parameter, the security rules, the import rules and conventions.
