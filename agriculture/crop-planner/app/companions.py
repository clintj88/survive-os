"""Companion planting database for the crop planner."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/companions", tags=["companions"])


class CompanionCreate(BaseModel):
    crop_a: str
    crop_b: str
    relationship: str
    notes: str = ""


@router.get("")
def list_companions(crop: Optional[str] = Query(None)) -> list[dict]:
    if crop:
        return query(
            """SELECT * FROM companions
               WHERE crop_a = ? OR crop_b = ?
               ORDER BY relationship, crop_a""",
            (crop, crop),
        )
    return query("SELECT * FROM companions ORDER BY crop_a, crop_b")


@router.get("/check")
def check_compatibility(crop_a: str, crop_b: str) -> dict:
    """Check compatibility between two crops."""
    results = query(
        """SELECT * FROM companions
           WHERE (crop_a = ? AND crop_b = ?) OR (crop_a = ? AND crop_b = ?)""",
        (crop_a, crop_b, crop_b, crop_a),
    )
    if results:
        return results[0]
    return {"crop_a": crop_a, "crop_b": crop_b, "relationship": "unknown", "notes": "No data available"}


@router.post("", status_code=201)
def create_companion(companion: CompanionCreate) -> dict:
    if companion.relationship not in ("beneficial", "neutral", "antagonistic"):
        raise HTTPException(status_code=400, detail="Relationship must be beneficial, neutral, or antagonistic")

    # Normalize ordering
    a, b = sorted([companion.crop_a, companion.crop_b])
    comp_id = execute(
        "INSERT OR REPLACE INTO companions (crop_a, crop_b, relationship, notes) VALUES (?, ?, ?, ?)",
        (a, b, companion.relationship, companion.notes),
    )
    results = query("SELECT * FROM companions WHERE id = ?", (comp_id,))
    return results[0]


@router.delete("/{companion_id}", status_code=204)
def delete_companion(companion_id: int) -> None:
    existing = query("SELECT id FROM companions WHERE id = ?", (companion_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Companion entry not found")
    execute("DELETE FROM companions WHERE id = ?", (companion_id,))
