"""Drone Aerial Maps API - SURVIVE OS Maps Module."""

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


app = FastAPI(title="SURVIVE OS Drone Aerial Maps", version=VERSION, lifespan=lifespan)

from .surveys import router as surveys_router
from .images import router as images_router
from .processing import router as processing_router
from .changes import router as changes_router
from .terrain import router as terrain_router

app.include_router(surveys_router)
app.include_router(images_router)
app.include_router(processing_router)
app.include_router(changes_router)
app.include_router(terrain_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
