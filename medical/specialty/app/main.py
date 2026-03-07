"""Medical Specialty Module - SURVIVE OS.

Provides prenatal/childbirth, dental, mental health, and veterinary care.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .prenatal import router as prenatal_router
from .dental import router as dental_router
from .mental import router as mental_router
from .veterinary import router as vet_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Medical Specialty", version=VERSION, lifespan=lifespan)

app.include_router(prenatal_router)
app.include_router(dental_router)
app.include_router(mental_router)
app.include_router(vet_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
