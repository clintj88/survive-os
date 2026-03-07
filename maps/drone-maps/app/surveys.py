"""Survey CRUD router for the drone-maps module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import VALID_SURVEY_STATUSES, execute, query

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


class SurveyCreate(BaseModel):
    name: str
    area_name: str = ""
    date: str = ""
    drone_model: str = ""
    operator: str = ""
    bounds: str = ""
    status: str = "planned"
    notes: str = ""


class SurveyUpdate(BaseModel):
    name: str | None = None
    area_name: str | None = None
    date: str | None = None
    drone_model: str | None = None
    operator: str | None = None
    bounds: str | None = None
    status: str | None = None
    notes: str | None = None


@router.get("")
def list_surveys(status: str = "", area_name: str = "") -> list[dict]:
    sql = "SELECT * FROM surveys WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if area_name:
        sql += " AND area_name LIKE ?"
        params.append(f"%{area_name}%")
    sql += " ORDER BY date DESC"
    return query(sql, tuple(params))


@router.get("/{survey_id}")
def get_survey(survey_id: int) -> dict:
    rows = query("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Survey not found")
    return rows[0]


@router.post("", status_code=201)
def create_survey(body: SurveyCreate) -> dict:
    if body.status and body.status not in VALID_SURVEY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_SURVEY_STATUSES}")
    date_val = body.date if body.date else None
    row_id = execute(
        """INSERT INTO surveys (name, area_name, date, drone_model, operator, bounds, status, notes)
           VALUES (?, ?, COALESCE(?, date('now')), ?, ?, ?, ?, ?)""",
        (body.name, body.area_name, date_val, body.drone_model, body.operator,
         body.bounds, body.status, body.notes),
    )
    return query("SELECT * FROM surveys WHERE id = ?", (row_id,))[0]


@router.put("/{survey_id}")
def update_survey(survey_id: int, body: SurveyUpdate) -> dict:
    existing = query("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Survey not found")
    if body.status is not None and body.status not in VALID_SURVEY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_SURVEY_STATUSES}")

    updates = {}
    for field in ("name", "area_name", "date", "drone_model", "operator", "bounds", "status", "notes"):
        val = getattr(body, field)
        if val is not None:
            updates[field] = val
    if not updates:
        return existing[0]

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [survey_id]
    execute(
        f"UPDATE surveys SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
        tuple(params),
    )
    return query("SELECT * FROM surveys WHERE id = ?", (survey_id,))[0]


@router.delete("/{survey_id}")
def delete_survey(survey_id: int) -> dict:
    existing = query("SELECT * FROM surveys WHERE id = ?", (survey_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Survey not found")
    execute("DELETE FROM change_detections WHERE survey_a_id = ? OR survey_b_id = ?", (survey_id, survey_id))
    execute("DELETE FROM terrain_models WHERE survey_id = ?", (survey_id,))
    execute("DELETE FROM processing_jobs WHERE survey_id = ?", (survey_id,))
    execute("DELETE FROM images WHERE survey_id = ?", (survey_id,))
    execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
    return {"detail": "Survey deleted"}


@router.get("/{survey_id}/compare/{other_id}")
def compare_surveys(survey_id: int, other_id: int) -> dict:
    for sid in (survey_id, other_id):
        if not query("SELECT id FROM surveys WHERE id = ?", (sid,)):
            raise HTTPException(status_code=404, detail=f"Survey {sid} not found")
    changes = query(
        """SELECT * FROM change_detections
           WHERE (survey_a_id = ? AND survey_b_id = ?)
              OR (survey_a_id = ? AND survey_b_id = ?)
           ORDER BY created_at DESC""",
        (survey_id, other_id, other_id, survey_id),
    )
    return {
        "survey_a_id": survey_id,
        "survey_b_id": other_id,
        "changes": changes,
    }
