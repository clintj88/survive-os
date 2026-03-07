"""Seed Bank Management API - SURVIVE OS Agriculture Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .inventory import router as inventory_router
from .germination import router as germination_router
from .viability import router as viability_router
from .diversity import router as diversity_router
from .exchange import router as exchange_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Seed Bank", version=VERSION, lifespan=lifespan)

app.include_router(inventory_router)
app.include_router(germination_router)
app.include_router(viability_router)
app.include_router(diversity_router)
app.include_router(exchange_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
