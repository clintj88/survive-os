"""Field and plot management for the crop planner."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/fields", tags=["fields"])


class FieldCreate(BaseModel):
    name: str
    rows: int = 4
    cols: int = 4
    description: str = ""


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    rows: Optional[int] = None
    cols: Optional[int] = None
    description: Optional[str] = None


class PlotAssignment(BaseModel):
    crop_id: int
    season: str
    year: int
    notes: str = ""


@router.get("")
def list_fields() -> list[dict]:
    return query("SELECT * FROM fields ORDER BY name")


@router.post("", status_code=201)
def create_field(field: FieldCreate) -> dict:
    field_id = execute(
        "INSERT INTO fields (name, rows, cols, description) VALUES (?, ?, ?, ?)",
        (field.name, field.rows, field.cols, field.description),
    )
    # Auto-create plots for the grid
    params_list = [
        (field_id, r, c, f"{chr(65 + r)}{c + 1}")
        for r in range(field.rows)
        for c in range(field.cols)
    ]
    from .database import execute_many
    execute_many(
        "INSERT INTO plots (field_id, row_idx, col_idx, label) VALUES (?, ?, ?, ?)",
        params_list,
    )
    return _get_field(field_id)


@router.get("/{field_id}")
def get_field(field_id: int) -> dict:
    return _get_field(field_id)


@router.put("/{field_id}")
def update_field(field_id: int, field: FieldUpdate) -> dict:
    existing = query("SELECT id FROM fields WHERE id = ?", (field_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Field not found")

    updates: list[str] = []
    params: list = []
    for attr in ("name", "description"):
        val = getattr(field, attr)
        if val is not None:
            updates.append(f"{attr} = ?")
            params.append(val)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(field_id)
    execute(f"UPDATE fields SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return _get_field(field_id)


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: int) -> None:
    existing = query("SELECT id FROM fields WHERE id = ?", (field_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Field not found")
    execute("DELETE FROM fields WHERE id = ?", (field_id,))


@router.get("/{field_id}/plots")
def list_plots(field_id: int) -> list[dict]:
    return query(
        """SELECT p.*, pa.crop_id, pa.season, pa.year, c.name as crop_name
           FROM plots p
           LEFT JOIN plot_assignments pa ON p.id = pa.plot_id
           LEFT JOIN crops c ON pa.crop_id = c.id
           WHERE p.field_id = ?
           ORDER BY p.row_idx, p.col_idx""",
        (field_id,),
    )


@router.post("/{field_id}/plots/{plot_id}/assign", status_code=201)
def assign_crop_to_plot(field_id: int, plot_id: int, assignment: PlotAssignment) -> dict:
    plot = query("SELECT id FROM plots WHERE id = ? AND field_id = ?", (plot_id, field_id))
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    crop = query("SELECT id FROM crops WHERE id = ?", (assignment.crop_id,))
    if not crop:
        raise HTTPException(status_code=400, detail="Crop not found")

    # Check for companion planting warnings
    warnings = _check_adjacent_companions(field_id, plot_id, assignment.crop_id, assignment.season, assignment.year)

    assign_id = execute(
        """INSERT OR REPLACE INTO plot_assignments (plot_id, crop_id, season, year, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (plot_id, assignment.crop_id, assignment.season, assignment.year, assignment.notes),
    )
    result = query(
        """SELECT pa.*, c.name as crop_name FROM plot_assignments pa
           JOIN crops c ON pa.crop_id = c.id WHERE pa.id = ?""",
        (assign_id,),
    )
    data = result[0] if result else {}
    if warnings:
        data["warnings"] = warnings
    return data


def _check_adjacent_companions(field_id: int, plot_id: int, crop_id: int, season: str, year: int) -> list[str]:
    """Check if adjacent plots have antagonistic companions."""
    plot_info = query("SELECT row_idx, col_idx FROM plots WHERE id = ?", (plot_id,))
    if not plot_info:
        return []
    row, col = plot_info[0]["row_idx"], plot_info[0]["col_idx"]

    crop_info = query("SELECT name FROM crops WHERE id = ?", (crop_id,))
    if not crop_info:
        return []
    crop_name = crop_info[0]["name"]

    # Get adjacent plots
    adjacent = query(
        """SELECT p.id, pa.crop_id, c.name as crop_name
           FROM plots p
           JOIN plot_assignments pa ON p.id = pa.plot_id
           JOIN crops c ON pa.crop_id = c.id
           WHERE p.field_id = ? AND pa.season = ? AND pa.year = ?
           AND abs(p.row_idx - ?) <= 1 AND abs(p.col_idx - ?) <= 1
           AND p.id != ?""",
        (field_id, season, year, row, col, plot_id),
    )

    warnings = []
    for adj in adjacent:
        companions = query(
            """SELECT relationship FROM companions
               WHERE (crop_a = ? AND crop_b = ?) OR (crop_a = ? AND crop_b = ?)""",
            (crop_name, adj["crop_name"], adj["crop_name"], crop_name),
        )
        for comp in companions:
            if comp["relationship"] == "antagonistic":
                warnings.append(f"{crop_name} is antagonistic with adjacent {adj['crop_name']}")
    return warnings


def _get_field(field_id: int) -> dict:
    results = query("SELECT * FROM fields WHERE id = ?", (field_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Field not found")
    field = results[0]
    field["plots"] = query(
        "SELECT * FROM plots WHERE field_id = ? ORDER BY row_idx, col_idx",
        (field_id,),
    )
    return field
