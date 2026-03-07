"""Engineering & Maintenance API - SURVIVE OS Resources Module."""

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
    # Seed data if tables are empty
    from .database import query
    existing = query("SELECT COUNT(*) as cnt FROM chemistry_recipes")
    if existing and existing[0]["cnt"] == 0:
        from seed.chemistry_recipes import seed_recipes
        from seed.example_guides import seed_guides
        seed_recipes()
        seed_guides()
    yield


app = FastAPI(title="SURVIVE OS Engineering & Maintenance", version=VERSION, lifespan=lifespan)


# Import and include routers
from .maintenance import router as maintenance_router
from .parts import router as parts_router
from .calculator import router as calculator_router
from .chemistry import router as chemistry_router
from .guides import router as guides_router
from .drawings import router as drawings_router

app.include_router(maintenance_router)
app.include_router(parts_router)
app.include_router(calculator_router)
app.include_router(chemistry_router)
app.include_router(guides_router)
app.include_router(drawings_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
