"""Technical Guides API routes."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/guides", tags=["guides"])


class GuideCreate(BaseModel):
    title: str
    category: str
    content: str
    parts_needed: list[str] = []
    difficulty: str = "medium"
    author: str = "system"


def _parse_guide(row: dict) -> dict:
    row["parts_needed"] = json.loads(row["parts_needed"])
    return row


@router.get("")
def list_guides(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        rows = query("SELECT * FROM technical_guides WHERE category = ? ORDER BY title", (category,))
    else:
        rows = query("SELECT * FROM technical_guides ORDER BY title")
    return [_parse_guide(r) for r in rows]


@router.post("", status_code=201)
def create_guide(guide: GuideCreate) -> dict:
    guide_id = execute(
        """INSERT INTO technical_guides (title, category, content, parts_needed, difficulty, author)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (guide.title, guide.category, guide.content, json.dumps(guide.parts_needed), guide.difficulty, guide.author),
    )
    rows = query("SELECT * FROM technical_guides WHERE id = ?", (guide_id,))
    return _parse_guide(rows[0])


@router.get("/search")
def search_guides(q: str = Query(..., min_length=1)) -> list[dict]:
    rows = query("SELECT * FROM technical_guides ORDER BY title")
    q_lower = q.lower()
    results = []
    for row in rows:
        if q_lower in row["title"].lower() or q_lower in row["content"].lower():
            results.append(_parse_guide(row))
    return results


@router.get("/{guide_id}")
def get_guide(guide_id: int) -> dict:
    rows = query("SELECT * FROM technical_guides WHERE id = ?", (guide_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _parse_guide(rows[0])
