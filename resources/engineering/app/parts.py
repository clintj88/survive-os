"""Parts Cross-Reference API routes."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/parts", tags=["parts"])


class PartCreate(BaseModel):
    part_number: str
    name: str
    category: str = ""
    description: str = ""
    fits_equipment: list[str] = []
    salvage_sources: list[str] = []
    quantity_on_hand: int = 0
    location: str = ""


class PartUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    fits_equipment: Optional[list[str]] = None
    salvage_sources: Optional[list[str]] = None
    quantity_on_hand: Optional[int] = None
    location: Optional[str] = None


def _parse_part(row: dict) -> dict:
    row["fits_equipment"] = json.loads(row["fits_equipment"])
    row["salvage_sources"] = json.loads(row["salvage_sources"])
    return row


@router.get("")
def list_parts(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        rows = query("SELECT * FROM parts WHERE category = ? ORDER BY name", (category,))
    else:
        rows = query("SELECT * FROM parts ORDER BY name")
    return [_parse_part(r) for r in rows]


@router.post("", status_code=201)
def create_part(part: PartCreate) -> dict:
    part_id = execute(
        """INSERT INTO parts (part_number, name, category, description, fits_equipment, salvage_sources, quantity_on_hand, location)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            part.part_number, part.name, part.category, part.description,
            json.dumps(part.fits_equipment), json.dumps(part.salvage_sources),
            part.quantity_on_hand, part.location,
        ),
    )
    rows = query("SELECT * FROM parts WHERE id = ?", (part_id,))
    return _parse_part(rows[0])


@router.get("/search")
def search_parts(equipment: str = Query(..., min_length=1)) -> list[dict]:
    rows = query("SELECT * FROM parts ORDER BY name")
    results = []
    for row in rows:
        fits = json.loads(row["fits_equipment"])
        if any(equipment.lower() in e.lower() for e in fits):
            results.append(_parse_part(row))
    return results


@router.get("/cross-reference")
def cross_reference(
    from_equipment: str = Query(..., min_length=1),
    to_equipment: str = Query(..., min_length=1),
) -> list[dict]:
    rows = query("SELECT * FROM parts ORDER BY name")
    results = []
    for row in rows:
        salvage = json.loads(row["salvage_sources"])
        fits = json.loads(row["fits_equipment"])
        from_match = any(from_equipment.lower() in s.lower() for s in salvage)
        to_match = any(to_equipment.lower() in e.lower() for e in fits)
        if from_match and to_match:
            results.append(_parse_part(row))
    return results


@router.get("/{part_id}")
def get_part(part_id: int) -> dict:
    rows = query("SELECT * FROM parts WHERE id = ?", (part_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Part not found")
    return _parse_part(rows[0])


@router.put("/{part_id}")
def update_part(part_id: int, part: PartUpdate) -> dict:
    existing = query("SELECT id FROM parts WHERE id = ?", (part_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Part not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "category", "description", "quantity_on_hand", "location"]:
        value = getattr(part, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if part.fits_equipment is not None:
        updates.append("fits_equipment = ?")
        params.append(json.dumps(part.fits_equipment))
    if part.salvage_sources is not None:
        updates.append("salvage_sources = ?")
        params.append(json.dumps(part.salvage_sources))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(part_id)
    execute(f"UPDATE parts SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_part(part_id)
