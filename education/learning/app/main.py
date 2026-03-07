"""Education & Learning API - SURVIVE OS Education Module."""

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
    existing = query("SELECT COUNT(*) as cnt FROM skill_checklists")
    if existing and existing[0]["cnt"] == 0:
        from seed.skill_checklists import seed_checklists
        from seed.lesson_plans import seed_lessons
        seed_checklists()
        seed_lessons()
    yield


app = FastAPI(title="SURVIVE OS Education & Learning", version=VERSION, lifespan=lifespan)

from .apprenticeship import router as apprenticeship_router
from .curriculum import router as curriculum_router
from .children import router as children_router
from .external import router as external_router

app.include_router(apprenticeship_router)
app.include_router(curriculum_router)
app.include_router(children_router)
app.include_router(external_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
