"""Technical Drawing Viewer API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/drawings", tags=["drawings"])


class DrawingCreate(BaseModel):
    title: str
    description: str = ""
    file_path: str
    category: str = ""
    related_equipment: str = ""


@router.get("")
def list_drawings(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        return query("SELECT * FROM technical_drawings WHERE category = ? ORDER BY title", (category,))
    return query("SELECT * FROM technical_drawings ORDER BY title")


@router.post("", status_code=201)
def create_drawing(drawing: DrawingCreate) -> dict:
    drawing_id = execute(
        """INSERT INTO technical_drawings (title, description, file_path, category, related_equipment)
           VALUES (?, ?, ?, ?, ?)""",
        (drawing.title, drawing.description, drawing.file_path, drawing.category, drawing.related_equipment),
    )
    rows = query("SELECT * FROM technical_drawings WHERE id = ?", (drawing_id,))
    return rows[0]


@router.get("/search")
def search_drawings(q: str = Query(..., min_length=1)) -> list[dict]:
    q_lower = q.lower()
    rows = query("SELECT * FROM technical_drawings ORDER BY title")
    return [r for r in rows if q_lower in r["title"].lower() or q_lower in r["description"].lower()]


@router.get("/{drawing_id}")
def get_drawing(drawing_id: int) -> dict:
    rows = query("SELECT * FROM technical_drawings WHERE id = ?", (drawing_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return rows[0]
