"""General Inventory API - SURVIVE OS Resources Module."""

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


app = FastAPI(title="SURVIVE OS General Inventory", version=VERSION, lifespan=lifespan)

from .items import router as items_router
from .scanning import router as scanning_router
from .consumption import router as consumption_router
from .alerts import router as alerts_router
from .locations import router as locations_router
from .audit import router as audit_router

app.include_router(items_router)
app.include_router(scanning_router)
app.include_router(consumption_router)
app.include_router(alerts_router)
app.include_router(locations_router)
app.include_router(audit_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
