"""EHR-Lite API - SURVIVE OS Medical Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .patients import router as patients_router
from .summary import router as summary_router
from .vaccinations import router as vaccinations_router
from .vaccinations import schedule_router as vaccine_schedule_router
from .visits import router as visits_router
from .vitals import router as vitals_router
from .wounds import router as wounds_router

config = load_config()
VERSION = config["version"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    yield


app = FastAPI(title="SURVIVE OS EHR-Lite", version=VERSION, lifespan=lifespan)

app.include_router(patients_router)
app.include_router(visits_router)
app.include_router(vitals_router)
app.include_router(wounds_router)
app.include_router(vaccinations_router)
app.include_router(vaccine_schedule_router)
app.include_router(summary_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
