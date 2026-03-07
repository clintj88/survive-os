"""Tileset registration and metadata router."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import VALID_FORMATS, execute, query

router = APIRouter(prefix="/api/tilesets", tags=["tilesets"])


class TilesetCreate(BaseModel):
    name: str
    filepath: str
    format: str = "pbf"
    description: str = ""
    min_zoom: int = 0
    max_zoom: int = 14
    bounds: str = "-180,-85.0511,180,85.0511"
    center_lat: float = 0.0
    center_lng: float = 0.0
    center_zoom: int = 2


class TilesetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    min_zoom: int | None = None
    max_zoom: int | None = None
    bounds: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    center_zoom: int | None = None


@router.get("")
def list_tilesets() -> list[dict]:
    return query("SELECT * FROM tilesets ORDER BY name")


@router.get("/{tileset_id}")
def get_tileset(tileset_id: int) -> dict:
    rows = query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Tileset not found")
    return rows[0]


@router.post("", status_code=201)
def create_tileset(body: TilesetCreate) -> dict:
    if body.format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format. Must be one of: {', '.join(VALID_FORMATS)}")

    if not Path(body.filepath).exists():
        raise HTTPException(status_code=400, detail="MBTiles file not found at specified path")

    try:
        tid = execute(
            """INSERT INTO tilesets (name, filepath, format, description, min_zoom, max_zoom,
               bounds, center_lat, center_lng, center_zoom)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (body.name, body.filepath, body.format, body.description,
             body.min_zoom, body.max_zoom, body.bounds,
             body.center_lat, body.center_lng, body.center_zoom),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Tileset with this name already exists")

    rows = query("SELECT * FROM tilesets WHERE id = ?", (tid,))
    return rows[0]


@router.put("/{tileset_id}")
def update_tileset(tileset_id: int, body: TilesetUpdate) -> dict:
    existing = query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Tileset not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return existing[0]

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [tileset_id]
    execute(
        f"UPDATE tilesets SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        tuple(values),
    )
    return query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))[0]


@router.delete("/{tileset_id}")
def delete_tileset(tileset_id: int) -> dict:
    existing = query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Tileset not found")
    execute("DELETE FROM tilesets WHERE id = ?", (tileset_id,))
    return {"detail": "Tileset deleted"}


@router.get("/{tileset_id}/tilejson")
def get_tilejson(tileset_id: int) -> dict:
    rows = query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Tileset not found")

    ts = rows[0]
    bounds = [float(b) for b in ts["bounds"].split(",")]
    center = [ts["center_lng"], ts["center_lat"], ts["center_zoom"]]

    return {
        "tilejson": "3.0.0",
        "name": ts["name"],
        "description": ts["description"],
        "format": ts["format"],
        "bounds": bounds,
        "center": center,
        "minzoom": ts["min_zoom"],
        "maxzoom": ts["max_zoom"],
        "tiles": [f"/api/tiles/{ts['name']}/{{z}}/{{x}}/{{y}}.{ts['format']}"],
    }
