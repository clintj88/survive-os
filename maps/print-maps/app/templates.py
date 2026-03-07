"""Print template CRUD router."""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .database import (
    VALID_DPI,
    VALID_ORIENTATIONS,
    VALID_PAPER_SIZES,
    VALID_TEMPLATE_TYPES,
    execute,
    query,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    template_type: str = "general"
    paper_size: str = "A4"
    orientation: str = "portrait"
    dpi: int = 300
    overlay_layers: list[str] = Field(default_factory=list)
    include_legend: bool = True
    include_scale_bar: bool = True
    include_north_arrow: bool = True
    include_grid: bool = False
    include_date: bool = True


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_type: str | None = None
    paper_size: str | None = None
    orientation: str | None = None
    dpi: int | None = None
    overlay_layers: list[str] | None = None
    include_legend: bool | None = None
    include_scale_bar: bool | None = None
    include_north_arrow: bool | None = None
    include_grid: bool | None = None
    include_date: bool | None = None


@router.post("", status_code=201)
def create_template(body: TemplateCreate) -> dict:
    if body.template_type not in VALID_TEMPLATE_TYPES:
        raise HTTPException(400, f"Invalid template_type. Must be one of: {VALID_TEMPLATE_TYPES}")
    if body.paper_size not in VALID_PAPER_SIZES:
        raise HTTPException(400, f"Invalid paper_size. Must be one of: {VALID_PAPER_SIZES}")
    if body.orientation not in VALID_ORIENTATIONS:
        raise HTTPException(400, f"Invalid orientation. Must be one of: {VALID_ORIENTATIONS}")
    if body.dpi not in VALID_DPI:
        raise HTTPException(400, f"Invalid dpi. Must be one of: {VALID_DPI}")

    existing = query("SELECT id FROM print_templates WHERE name = ?", (body.name,))
    if existing:
        raise HTTPException(400, "Template with this name already exists")

    layers_json = json.dumps(body.overlay_layers)
    tmpl_id = execute(
        """INSERT INTO print_templates
           (name, description, template_type, paper_size, orientation, dpi,
            overlay_layers, include_legend, include_scale_bar,
            include_north_arrow, include_grid, include_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body.name, body.description, body.template_type,
            body.paper_size, body.orientation, body.dpi, layers_json,
            int(body.include_legend), int(body.include_scale_bar),
            int(body.include_north_arrow), int(body.include_grid),
            int(body.include_date),
        ),
    )
    rows = query("SELECT * FROM print_templates WHERE id = ?", (tmpl_id,))
    return _format_template(rows[0])


@router.get("")
def list_templates(template_type: str | None = None) -> list[dict]:
    if template_type:
        rows = query(
            "SELECT * FROM print_templates WHERE template_type = ? ORDER BY name",
            (template_type,),
        )
    else:
        rows = query("SELECT * FROM print_templates ORDER BY name")
    return [_format_template(r) for r in rows]


@router.get("/{template_id}")
def get_template(template_id: int) -> dict:
    rows = query("SELECT * FROM print_templates WHERE id = ?", (template_id,))
    if not rows:
        raise HTTPException(404, "Template not found")
    return _format_template(rows[0])


@router.put("/{template_id}")
def update_template(template_id: int, body: TemplateUpdate) -> dict:
    rows = query("SELECT * FROM print_templates WHERE id = ?", (template_id,))
    if not rows:
        raise HTTPException(404, "Template not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return _format_template(rows[0])

    if "template_type" in updates and updates["template_type"] not in VALID_TEMPLATE_TYPES:
        raise HTTPException(400, f"Invalid template_type. Must be one of: {VALID_TEMPLATE_TYPES}")
    if "paper_size" in updates and updates["paper_size"] not in VALID_PAPER_SIZES:
        raise HTTPException(400, f"Invalid paper_size. Must be one of: {VALID_PAPER_SIZES}")
    if "orientation" in updates and updates["orientation"] not in VALID_ORIENTATIONS:
        raise HTTPException(400, f"Invalid orientation. Must be one of: {VALID_ORIENTATIONS}")
    if "dpi" in updates and updates["dpi"] not in VALID_DPI:
        raise HTTPException(400, f"Invalid dpi. Must be one of: {VALID_DPI}")

    if "overlay_layers" in updates:
        updates["overlay_layers"] = json.dumps(updates["overlay_layers"])
    for field in ("include_legend", "include_scale_bar", "include_north_arrow", "include_grid", "include_date"):
        if field in updates:
            updates[field] = int(updates[field])

    if "name" in updates:
        existing = query(
            "SELECT id FROM print_templates WHERE name = ? AND id != ?",
            (updates["name"], template_id),
        )
        if existing:
            raise HTTPException(400, "Template with this name already exists")

    set_clauses = ", ".join(f"{k} = ?" for k in updates)
    set_clauses += ", updated_at = datetime('now')"
    params = list(updates.values()) + [template_id]
    execute(f"UPDATE print_templates SET {set_clauses} WHERE id = ?", tuple(params))

    rows = query("SELECT * FROM print_templates WHERE id = ?", (template_id,))
    return _format_template(rows[0])


@router.delete("/{template_id}")
def delete_template(template_id: int) -> dict:
    rows = query("SELECT * FROM print_templates WHERE id = ?", (template_id,))
    if not rows:
        raise HTTPException(404, "Template not found")
    execute("DELETE FROM print_templates WHERE id = ?", (template_id,))
    return {"deleted": template_id}


def _format_template(row: dict) -> dict:
    tmpl = dict(row)
    tmpl["overlay_layers"] = json.loads(tmpl.get("overlay_layers", "[]"))
    for field in (
        "include_legend", "include_scale_bar", "include_north_arrow",
        "include_grid", "include_date",
    ):
        tmpl[field] = bool(tmpl.get(field))
    return tmpl
