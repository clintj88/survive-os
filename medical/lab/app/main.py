"""Lab Results Tracking API - SURVIVE OS Medical Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .catalog import router as catalog_router
from .orders import router as orders_router
from .panels import router as panels_router
from .results import router as results_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    # Seed common tests on startup
    from seed.common_tests import seed
    seed()
    yield


app = FastAPI(title="SURVIVE OS Lab Results", version=VERSION, lifespan=lifespan)

app.include_router(catalog_router)
app.include_router(panels_router)
app.include_router(orders_router)
app.include_router(results_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
