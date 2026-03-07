"""Printable Map Generation API - SURVIVE OS Maps Module."""

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


app = FastAPI(title="SURVIVE OS Printable Maps", version=VERSION, lifespan=lifespan)

from .jobs import router as jobs_router, set_output_dir
from .templates import router as templates_router

set_output_dir(config["output_dir"])
app.include_router(jobs_router)
app.include_router(templates_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
