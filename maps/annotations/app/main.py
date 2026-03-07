"""Community Map Annotations API - SURVIVE OS Maps Module."""

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


app = FastAPI(title="SURVIVE OS Map Annotations", version=VERSION, lifespan=lifespan)

from .layers import router as layers_router
from .annotations import router as annotations_router
from .geojson import router as geojson_router

app.include_router(layers_router)
app.include_router(annotations_router)
app.include_router(geojson_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
