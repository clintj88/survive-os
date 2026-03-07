"""Offline Map Tile Server - SURVIVE OS Maps Module."""

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


app = FastAPI(title="SURVIVE OS Tile Server", version=VERSION, lifespan=lifespan)

from .tiles import router as tiles_router
from .tilesets import router as tilesets_router
from .styles import router as styles_router

app.include_router(tiles_router)
app.include_router(tilesets_router)
app.include_router(styles_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
