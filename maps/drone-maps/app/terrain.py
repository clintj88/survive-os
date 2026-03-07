"""Terrain model metadata router for the drone-maps module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/terrain", tags=["terrain"])


class TerrainCreate(BaseModel):
    survey_id: int
    filepath: str
    resolution: float | None = None
    bounds: str = ""


@router.get("")
def list_terrain(survey_id: int | None = None) -> list[dict]:
    if survey_id is not None:
        return query("SELECT * FROM terrain_models WHERE survey_id = ? ORDER BY created_at DESC", (survey_id,))
    return query("SELECT * FROM terrain_models ORDER BY created_at DESC")


@router.get("/{terrain_id}")
def get_terrain(terrain_id: int) -> dict:
    rows = query("SELECT * FROM terrain_models WHERE id = ?", (terrain_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Terrain model not found")
    return rows[0]


@router.post("", status_code=201)
def create_terrain(body: TerrainCreate) -> dict:
    if not query("SELECT id FROM surveys WHERE id = ?", (body.survey_id,)):
        raise HTTPException(status_code=404, detail="Survey not found")
    row_id = execute(
        """INSERT INTO terrain_models (survey_id, filepath, resolution, bounds)
           VALUES (?, ?, ?, ?)""",
        (body.survey_id, body.filepath, body.resolution, body.bounds),
    )
    return query("SELECT * FROM terrain_models WHERE id = ?", (row_id,))[0]


@router.delete("/{terrain_id}")
def delete_terrain(terrain_id: int) -> dict:
    rows = query("SELECT * FROM terrain_models WHERE id = ?", (terrain_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Terrain model not found")
    execute("DELETE FROM terrain_models WHERE id = ?", (terrain_id,))
    return {"detail": "Terrain model deleted"}
