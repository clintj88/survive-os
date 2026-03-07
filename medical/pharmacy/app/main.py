"""Pharmacy API - SURVIVE OS Medical Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .dosage import router as dosage_router
from .interactions import router as interactions_router
from .inventory import router as inventory_router
from .natural import router as natural_router
from .prescriptions import router as prescriptions_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Pharmacy", version=VERSION, lifespan=lifespan)

app.include_router(inventory_router)
app.include_router(prescriptions_router)
app.include_router(interactions_router)
app.include_router(natural_router)
app.include_router(dosage_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
