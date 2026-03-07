"""Tool Library API - SURVIVE OS Resources Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Tool Library", version=VERSION, lifespan=lifespan)

from .inventory import router as inventory_router
from .checkout import router as checkout_router
from .maintenance import router as maintenance_router
from .usage import router as usage_router
from .reservations import router as reservations_router

app.include_router(inventory_router)
app.include_router(checkout_router)
app.include_router(maintenance_router)
app.include_router(usage_router)
app.include_router(reservations_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
