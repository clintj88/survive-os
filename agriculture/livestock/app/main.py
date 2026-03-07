"""Livestock Management API - SURVIVE OS Agriculture Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .animals import router as animals_router
from .breeding import router as breeding_router
from .config import load_config
from .database import init_db, set_db_path
from .feed import router as feed_router
from .production import router as production_router
from .veterinary import router as vet_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    _seed_if_empty()
    yield


def _seed_if_empty() -> None:
    from .database import query
    reqs = query("SELECT COUNT(*) as c FROM feed_requirements")
    if reqs[0]["c"] == 0:
        from seed.feed_data import seed_feed_data
        seed_feed_data()


app = FastAPI(title="SURVIVE OS Livestock Management", version=VERSION, lifespan=lifespan)

app.include_router(animals_router)
app.include_router(breeding_router)
app.include_router(feed_router)
app.include_router(vet_router)
app.include_router(production_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
