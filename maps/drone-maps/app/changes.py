"""Change detection router for the drone-maps module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import VALID_CHANGE_TYPES, VALID_SEVERITIES, execute, query

router = APIRouter(prefix="/api/changes", tags=["changes"])


class ChangeCreate(BaseModel):
    survey_a_id: int
    survey_b_id: int
    change_type: str
    geometry: str = ""
    description: str = ""
    severity: str = "low"


@router.get("")
def list_changes(survey_a_id: int | None = None, survey_b_id: int | None = None) -> list[dict]:
    sql = "SELECT * FROM change_detections WHERE 1=1"
    params: list = []
    if survey_a_id is not None:
        sql += " AND survey_a_id = ?"
        params.append(survey_a_id)
    if survey_b_id is not None:
        sql += " AND survey_b_id = ?"
        params.append(survey_b_id)
    sql += " ORDER BY created_at DESC"
    return query(sql, tuple(params))


@router.get("/{change_id}")
def get_change(change_id: int) -> dict:
    rows = query("SELECT * FROM change_detections WHERE id = ?", (change_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Change detection not found")
    return rows[0]


@router.post("", status_code=201)
def create_change(body: ChangeCreate) -> dict:
    if body.change_type not in VALID_CHANGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid change_type. Must be one of: {VALID_CHANGE_TYPES}")
    if body.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {VALID_SEVERITIES}")
    for sid in (body.survey_a_id, body.survey_b_id):
        if not query("SELECT id FROM surveys WHERE id = ?", (sid,)):
            raise HTTPException(status_code=404, detail=f"Survey {sid} not found")
    row_id = execute(
        """INSERT INTO change_detections (survey_a_id, survey_b_id, change_type, geometry, description, severity)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (body.survey_a_id, body.survey_b_id, body.change_type,
         body.geometry, body.description, body.severity),
    )
    return query("SELECT * FROM change_detections WHERE id = ?", (row_id,))[0]


@router.delete("/{change_id}")
def delete_change(change_id: int) -> dict:
    rows = query("SELECT * FROM change_detections WHERE id = ?", (change_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Change detection not found")
    execute("DELETE FROM change_detections WHERE id = ?", (change_id,))
    return {"detail": "Change detection deleted"}
