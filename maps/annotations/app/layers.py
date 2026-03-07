"""Layer management routes for the map annotations module."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import VALID_LAYER_TYPES, execute, query

router = APIRouter(prefix="/api/layers", tags=["layers"])


class LayerCreate(BaseModel):
    name: str
    type: str
    color: str = "#4facfe"
    visible: bool = True
    description: str = ""


class LayerUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    color: str | None = None
    visible: bool | None = None
    description: str | None = None


@router.post("", status_code=201)
def create_layer(body: LayerCreate) -> dict:
    if body.type not in VALID_LAYER_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid layer type. Must be one of: {', '.join(VALID_LAYER_TYPES)}")
    layer_id = execute(
        "INSERT INTO layers (name, type, color, visible, description) VALUES (?, ?, ?, ?, ?)",
        (body.name, body.type, body.color, int(body.visible), body.description),
    )
    rows = query("SELECT * FROM layers WHERE id = ?", (layer_id,))
    return _format_layer(rows[0])


@router.get("")
def list_layers() -> list[dict]:
    rows = query("""
        SELECT l.*, COUNT(a.id) as annotation_count
        FROM layers l
        LEFT JOIN annotations a ON a.layer_id = l.id
        GROUP BY l.id
        ORDER BY l.created_at DESC
    """)
    return [_format_layer(r) for r in rows]


@router.get("/{layer_id}")
def get_layer(layer_id: int) -> dict:
    rows = query("SELECT * FROM layers WHERE id = ?", (layer_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Layer not found")
    return _format_layer(rows[0])


@router.put("/{layer_id}")
def update_layer(layer_id: int, body: LayerUpdate) -> dict:
    rows = query("SELECT * FROM layers WHERE id = ?", (layer_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Layer not found")
    if body.type is not None and body.type not in VALID_LAYER_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid layer type. Must be one of: {', '.join(VALID_LAYER_TYPES)}")
    updates = []
    params: list = []
    for field in ("name", "type", "color", "description"):
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if body.visible is not None:
        updates.append("visible = ?")
        params.append(int(body.visible))
    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        params.append(layer_id)
        execute(f"UPDATE layers SET {', '.join(updates)} WHERE id = ?", tuple(params))
    rows = query("SELECT * FROM layers WHERE id = ?", (layer_id,))
    return _format_layer(rows[0])


@router.delete("/{layer_id}")
def delete_layer(layer_id: int) -> dict:
    rows = query("SELECT * FROM layers WHERE id = ?", (layer_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Layer not found")
    execute("DELETE FROM annotations WHERE layer_id = ?", (layer_id,))
    execute("DELETE FROM layers WHERE id = ?", (layer_id,))
    return {"detail": "Layer deleted"}


def _format_layer(row: dict) -> dict:
    result = dict(row)
    result["visible"] = bool(result["visible"])
    return result
