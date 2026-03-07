"""Annotation management routes for the map annotations module."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import VALID_CATEGORIES, execute, query

router = APIRouter(prefix="/api/annotations", tags=["annotations"])


class AnnotationCreate(BaseModel):
    layer_id: int
    geometry: dict
    category: str
    title: str = ""
    description: str = ""
    properties: dict | None = None
    creator: str = ""
    radius_meters: float | None = None
    latitude: float | None = None
    longitude: float | None = None


class AnnotationUpdate(BaseModel):
    geometry: dict | None = None
    category: str | None = None
    title: str | None = None
    description: str | None = None
    properties: dict | None = None
    creator: str | None = None
    radius_meters: float | None = None
    latitude: float | None = None
    longitude: float | None = None


@router.post("", status_code=201)
def create_annotation(body: AnnotationCreate) -> dict:
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    layers = query("SELECT id FROM layers WHERE id = ?", (body.layer_id,))
    if not layers:
        raise HTTPException(status_code=404, detail="Layer not found")
    crdt_id = str(uuid.uuid4())
    geometry_json = json.dumps(body.geometry)
    properties_json = json.dumps(body.properties or {})
    ann_id = execute(
        """INSERT INTO annotations
           (layer_id, geometry, category, title, description, properties, creator, crdt_id, radius_meters, latitude, longitude)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.layer_id, geometry_json, body.category, body.title, body.description,
         properties_json, body.creator, crdt_id, body.radius_meters, body.latitude, body.longitude),
    )
    rows = query("SELECT * FROM annotations WHERE id = ?", (ann_id,))
    return _format_annotation(rows[0])


@router.get("")
def list_annotations(layer_id: int | None = None) -> list[dict]:
    if layer_id is not None:
        rows = query("SELECT * FROM annotations WHERE layer_id = ? ORDER BY created_at DESC", (layer_id,))
    else:
        rows = query("SELECT * FROM annotations ORDER BY created_at DESC")
    return [_format_annotation(r) for r in rows]


@router.get("/search")
def search_annotations(
    min_lat: float = Query(...),
    min_lng: float = Query(...),
    max_lat: float = Query(...),
    max_lng: float = Query(...),
) -> list[dict]:
    rows = query(
        """SELECT * FROM annotations
           WHERE latitude >= ? AND latitude <= ? AND longitude >= ? AND longitude <= ?
           ORDER BY created_at DESC""",
        (min_lat, max_lat, min_lng, max_lng),
    )
    return [_format_annotation(r) for r in rows]


@router.get("/{annotation_id}")
def get_annotation(annotation_id: int) -> dict:
    rows = query("SELECT * FROM annotations WHERE id = ?", (annotation_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return _format_annotation(rows[0])


@router.put("/{annotation_id}")
def update_annotation(annotation_id: int, body: AnnotationUpdate) -> dict:
    rows = query("SELECT * FROM annotations WHERE id = ?", (annotation_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Annotation not found")
    if body.category is not None and body.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    updates = []
    params: list = []
    for field in ("category", "title", "description", "creator"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if body.geometry is not None:
        updates.append("geometry = ?")
        params.append(json.dumps(body.geometry))
    if body.properties is not None:
        updates.append("properties = ?")
        params.append(json.dumps(body.properties))
    for field in ("radius_meters", "latitude", "longitude"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        params.append(annotation_id)
        execute(f"UPDATE annotations SET {', '.join(updates)} WHERE id = ?", tuple(params))
    rows = query("SELECT * FROM annotations WHERE id = ?", (annotation_id,))
    return _format_annotation(rows[0])


@router.delete("/{annotation_id}")
def delete_annotation(annotation_id: int) -> dict:
    rows = query("SELECT * FROM annotations WHERE id = ?", (annotation_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Annotation not found")
    execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
    return {"detail": "Annotation deleted"}


def _format_annotation(row: dict) -> dict:
    result = dict(row)
    result["geometry"] = json.loads(result["geometry"])
    result["properties"] = json.loads(result["properties"])
    return result
