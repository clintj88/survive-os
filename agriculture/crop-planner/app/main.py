"""Crop Rotation Planner API - SURVIVE OS Agriculture Module."""

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
    # Seed default data if tables are empty
    from .database import query
    if not query("SELECT id FROM crops LIMIT 1"):
        from seed.companions import seed_companions
        from seed.rotations import seed_defaults
        seed_defaults()
        seed_companions()
    yield


app = FastAPI(title="SURVIVE OS Crop Rotation Planner", version=VERSION, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# Crop CRUD (simple, inline)
from typing import Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel

from .database import execute, query


class CropCreate(BaseModel):
    name: str
    family: str = ""
    rotation_group: str = ""
    days_to_maturity: int = 90
    sow_indoor_offset: Optional[int] = None
    sow_outdoor_offset: Optional[int] = None
    transplant_offset: Optional[int] = None
    harvest_start_offset: Optional[int] = None
    harvest_end_offset: Optional[int] = None
    notes: str = ""


@app.get("/api/crops")
def list_crops(group: Optional[str] = Query(None)) -> list[dict]:
    if group:
        return query("SELECT * FROM crops WHERE rotation_group = ? ORDER BY name", (group,))
    return query("SELECT * FROM crops ORDER BY name")


@app.get("/api/crops/{crop_id}")
def get_crop(crop_id: int) -> dict:
    results = query("SELECT * FROM crops WHERE id = ?", (crop_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Crop not found")
    return results[0]


@app.post("/api/crops", status_code=201)
def create_crop(crop: CropCreate) -> dict:
    crop_id = execute(
        """INSERT INTO crops (name, family, rotation_group, days_to_maturity,
           sow_indoor_offset, sow_outdoor_offset, transplant_offset,
           harvest_start_offset, harvest_end_offset, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (crop.name, crop.family, crop.rotation_group, crop.days_to_maturity,
         crop.sow_indoor_offset, crop.sow_outdoor_offset, crop.transplant_offset,
         crop.harvest_start_offset, crop.harvest_end_offset, crop.notes),
    )
    return get_crop(crop_id)


# Include routers
from .fields import router as fields_router
from .rotations import router as rotations_router
from .companions import router as companions_router
from .calendar import router as calendar_router
from .yields import router as yields_router

app.include_router(fields_router)
app.include_router(rotations_router)
app.include_router(companions_router)
app.include_router(calendar_router)
app.include_router(yields_router)

# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
