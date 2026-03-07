"""Trade & Barter Ledger API - SURVIVE OS Resources Module."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .ledger import router as ledger_router
from .rates import router as rates_router
from .history import router as history_router
from .market import router as market_router, set_redis
from .skills import router as skills_router

logger = logging.getLogger("survive-trade")
config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()

    # Seed default exchange rates if table is empty
    from .database import query
    if not query("SELECT 1 FROM exchange_rates LIMIT 1"):
        from seed.exchange_rates import seed_rates
        seed_rates()

    # Try to connect to Redis (optional)
    try:
        import redis
        client = redis.Redis.from_url(config["redis"]["url"])
        client.ping()
        set_redis(client)
        logger.info("Connected to Redis at %s", config["redis"]["url"])
    except Exception:
        logger.info("Redis not available, market announcements disabled")

    yield


app = FastAPI(title="SURVIVE OS Trade & Barter Ledger", version=VERSION, lifespan=lifespan)

app.include_router(ledger_router)
app.include_router(rates_router)
app.include_router(history_router)
app.include_router(market_router)
app.include_router(skills_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
