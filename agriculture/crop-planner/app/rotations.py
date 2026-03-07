"""Rotation templates and scheduling for the crop planner."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, execute_many, query

router = APIRouter(prefix="/api/rotations", tags=["rotations"])

ROTATION_ORDER = ["legume", "leaf", "fruit", "root"]


class RotationTemplateCreate(BaseModel):
    name: str
    climate_zone: str = "temperate"
    description: str = ""
    steps: list[dict] = []


class RotationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    climate_zone: Optional[str] = None
    description: Optional[str] = None


@router.get("/templates")
def list_templates() -> list[dict]:
    templates = query("SELECT * FROM rotation_templates ORDER BY name")
    for t in templates:
        t["steps"] = query(
            "SELECT * FROM rotation_steps WHERE template_id = ? ORDER BY year_offset",
            (t["id"],),
        )
    return templates


@router.post("/templates", status_code=201)
def create_template(template: RotationTemplateCreate) -> dict:
    template_id = execute(
        "INSERT INTO rotation_templates (name, climate_zone, description) VALUES (?, ?, ?)",
        (template.name, template.climate_zone, template.description),
    )
    if template.steps:
        execute_many(
            "INSERT INTO rotation_steps (template_id, year_offset, rotation_group, notes) VALUES (?, ?, ?, ?)",
            [(template_id, s.get("year_offset", i), s["rotation_group"], s.get("notes", ""))
             for i, s in enumerate(template.steps)],
        )
    return _get_template(template_id)


@router.get("/templates/{template_id}")
def get_template(template_id: int) -> dict:
    return _get_template(template_id)


@router.put("/templates/{template_id}")
def update_template(template_id: int, template: RotationTemplateUpdate) -> dict:
    existing = query("SELECT id FROM rotation_templates WHERE id = ?", (template_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    updates: list[str] = []
    params: list = []
    for attr in ("name", "climate_zone", "description"):
        val = getattr(template, attr)
        if val is not None:
            updates.append(f"{attr} = ?")
            params.append(val)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(template_id)
    execute(f"UPDATE rotation_templates SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return _get_template(template_id)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: int) -> None:
    existing = query("SELECT id FROM rotation_templates WHERE id = ?", (template_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    execute("DELETE FROM rotation_templates WHERE id = ?", (template_id,))


@router.get("/suggest/{plot_id}")
def suggest_next_crop(plot_id: int, year: int = 2026, season: str = "spring") -> dict:
    """Suggest the next crop for a plot based on rotation history."""
    # Get the last few assignments for this plot
    history = query(
        """SELECT pa.*, c.name as crop_name, c.rotation_group
           FROM plot_assignments pa
           JOIN crops c ON pa.crop_id = c.id
           WHERE pa.plot_id = ?
           ORDER BY pa.year DESC, pa.season DESC
           LIMIT 4""",
        (plot_id,),
    )

    if not history:
        return {
            "plot_id": plot_id,
            "suggestion": "legume",
            "reason": "No planting history - start rotation with legumes to fix nitrogen",
            "candidates": _get_crops_by_group("legume"),
        }

    last_group = history[0]["rotation_group"]
    if last_group in ROTATION_ORDER:
        idx = ROTATION_ORDER.index(last_group)
        next_group = ROTATION_ORDER[(idx + 1) % len(ROTATION_ORDER)]
    else:
        next_group = "legume"

    return {
        "plot_id": plot_id,
        "suggestion": next_group,
        "reason": f"Last crop was {history[0]['crop_name']} ({last_group}), next in rotation: {next_group}",
        "history": [{"crop": h["crop_name"], "group": h["rotation_group"], "year": h["year"], "season": h["season"]} for h in history],
        "candidates": _get_crops_by_group(next_group),
    }


def _get_crops_by_group(group: str) -> list[dict]:
    return query("SELECT id, name, family, days_to_maturity FROM crops WHERE rotation_group = ?", (group,))


def _get_template(template_id: int) -> dict:
    results = query("SELECT * FROM rotation_templates WHERE id = ?", (template_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Template not found")
    template = results[0]
    template["steps"] = query(
        "SELECT * FROM rotation_steps WHERE template_id = ? ORDER BY year_offset",
        (template_id,),
    )
    return template
