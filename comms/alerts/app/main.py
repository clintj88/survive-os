"""Emergency Alert System - SURVIVE OS Communications Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .broadcaster import init_redis
from .config import load_config
from .database import init_db, set_db_path
from .routes import router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    redis_cfg = config.get("redis", {})
    init_redis(redis_cfg.get("host", "localhost"), redis_cfg.get("port", 6379))
    yield


app = FastAPI(title="SURVIVE OS Emergency Alerts", version=VERSION, lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
