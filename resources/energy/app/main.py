"""Energy & Fuel Tracking API - SURVIVE OS Resources Module."""

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


app = FastAPI(title="SURVIVE OS Energy & Fuel Tracking", version=VERSION, lifespan=lifespan)

from .solar import router as solar_router
from .batteries import router as batteries_router
from .fuel import router as fuel_router
from .generators import router as generators_router
from .budget import router as budget_router

app.include_router(solar_router)
app.include_router(batteries_router)
app.include_router(fuel_router)
app.include_router(generators_router)
app.include_router(budget_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
