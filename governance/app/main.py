"""Governance API - SURVIVE OS Governance Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path

from .census import router as census_router
from .voting import router as voting_router
from .resources import router as resources_router
from .treaties import router as treaties_router
from .disputes import router as disputes_router
from .duties import router as duties_router
from .journal import router as journal_router
from .registry import router as registry_router
from .calendar_mod import router as calendar_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Governance", version=VERSION, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


app.include_router(census_router)
app.include_router(voting_router)
app.include_router(resources_router)
app.include_router(treaties_router)
app.include_router(disputes_router)
app.include_router(duties_router)
app.include_router(journal_router)
app.include_router(registry_router)
app.include_router(calendar_router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
