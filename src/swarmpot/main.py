import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from swarmpot.ledger.router import router as ledger_router
from swarmpot.proxy.router import router as proxy_router
from swarmpot.redact_payment_filter import RedactPaymentFilter

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.getLogger("uvicorn.access").addFilter(RedactPaymentFilter())
    yield


app = FastAPI(title="swarmpot", lifespan=lifespan)
app.include_router(proxy_router)
app.include_router(ledger_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the built Svelte app (npm run build) from the same origin as the API.
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
