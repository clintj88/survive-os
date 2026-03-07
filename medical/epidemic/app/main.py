"""Epidemic Surveillance API - SURVIVE OS Medical Module."""

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
    set_db_path(config["database"]["path"], config["database"]["key"])
    init_db()
    yield


app = FastAPI(title="SURVIVE OS Epidemic Surveillance", version=VERSION, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Register routers
from .surveillance import router as surveillance_router  # noqa: E402
from .alerts import router as alerts_router  # noqa: E402
from .sharing import router as sharing_router  # noqa: E402
from .contacts import router as contacts_router  # noqa: E402
from .quarantine import router as quarantine_router  # noqa: E402
from .timeline import router as timeline_router  # noqa: E402

app.include_router(surveillance_router)
app.include_router(alerts_router)
app.include_router(sharing_router)
app.include_router(contacts_router)
app.include_router(quarantine_router)
app.include_router(timeline_router)

# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
