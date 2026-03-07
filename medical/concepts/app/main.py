"""Clinical Concept Dictionary API - SURVIVE OS Medical Module."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .concepts import router as concepts_router
from .mappings import router as mappings_router
from .sets import router as sets_router

config = load_config()
VERSION = config["version"]


def _seed_data() -> None:
    """Load seed data if the concepts table is empty."""
    from .database import query
    rows = query("SELECT COUNT(*) as cnt FROM concepts")
    if rows[0]["cnt"] == 0:
        from seed.clinical_concepts import seed_all
        seed_all()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"], config["database"].get("key", ""))
    init_db()
    _seed_data()
    yield


app = FastAPI(title="SURVIVE OS Clinical Concepts", version=VERSION, lifespan=lifespan)

app.include_router(concepts_router)
app.include_router(mappings_router)
app.include_router(sets_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
