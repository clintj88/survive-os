"""GeoJSON import/export routes for the map annotations module."""

import json
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import VALID_CATEGORIES, execute, query

router = APIRouter(prefix="/api/geojson", tags=["geojson"])


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[dict]


@router.get("/export")
def export_geojson(layer_id: int = Query(...)) -> dict:
    layers = query("SELECT id FROM layers WHERE id = ?", (layer_id,))
    if not layers:
        raise HTTPException(status_code=404, detail="Layer not found")
    rows = query("SELECT * FROM annotations WHERE layer_id = ?", (layer_id,))
    features = []
    for row in rows:
        props = json.loads(row["properties"])
        props.update({
            "id": row["id"],
            "category": row["category"],
            "title": row["title"],
            "description": row["description"],
            "creator": row["creator"],
            "crdt_id": row["crdt_id"],
        })
        if row["radius_meters"] is not None:
            props["radius_meters"] = row["radius_meters"]
        features.append({
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


@router.post("/import", status_code=201)
def import_geojson(body: FeatureCollection, layer_id: int = Query(...)) -> dict:
    layers = query("SELECT id FROM layers WHERE id = ?", (layer_id,))
    if not layers:
        raise HTTPException(status_code=404, detail="Layer not found")
    imported = 0
    errors = []
    for i, feature in enumerate(body.features):
        try:
            geometry = feature.get("geometry")
            if not geometry:
                errors.append({"index": i, "error": "Missing geometry"})
                continue
            props = feature.get("properties", {})
            category = props.get("category", "water_source")
            if category not in VALID_CATEGORIES:
                category = "water_source"
            title = props.get("title", "")
            description = props.get("description", "")
            creator = props.get("creator", "")
            radius_meters = props.get("radius_meters")
            crdt_id = props.get("crdt_id") or str(uuid.uuid4())
            latitude = props.get("latitude")
            longitude = props.get("longitude")
            # Extract lat/lng from Point geometry if not in properties
            if latitude is None and geometry.get("type") == "Point":
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:
                    longitude = coords[0]
                    latitude = coords[1]
            # Remove metadata keys from properties before storing
            stored_props = {k: v for k, v in props.items()
                           if k not in ("id", "category", "title", "description", "creator",
                                        "crdt_id", "radius_meters", "latitude", "longitude")}
            execute(
                """INSERT INTO annotations
                   (layer_id, geometry, category, title, description, properties, creator, crdt_id, radius_meters, latitude, longitude)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (layer_id, json.dumps(geometry), category, title, description,
                 json.dumps(stored_props), creator, crdt_id, radius_meters, latitude, longitude),
            )
            imported += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    return {"imported": imported, "errors": errors}
