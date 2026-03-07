"""Program Enrollment API - SURVIVE OS Medical Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .enrollments import router as enrollments_router
from .programs import router as programs_router
from .workflows import router as workflows_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    # Seed default programs
    from seed.programs import seed
    seed()
    yield


app = FastAPI(title="SURVIVE OS Program Enrollment", version=VERSION, lifespan=lifespan)

app.include_router(programs_router)
app.include_router(workflows_router)
app.include_router(enrollments_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
