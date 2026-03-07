"""Program definitions CRUD endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/programs", tags=["programs"])


class ProgramCreate(BaseModel):
    name: str
    description: str = ""
    active: bool = True


class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
def list_programs(user: str = Depends(require_medical_role)) -> list[dict]:
    return query("SELECT * FROM programs ORDER BY name")


@router.get("/dashboard")
def dashboard(user: str = Depends(require_medical_role)) -> list[dict]:
    """Per-program counts by current state."""
    programs = query("SELECT * FROM programs WHERE active = 1 ORDER BY name")
    result = []
    for prog in programs:
        # Get active enrollment count
        active_count = query(
            "SELECT COUNT(*) as count FROM enrollments WHERE program_id = ? AND outcome = 'active'",
            (prog["id"],),
        )[0]["count"]

        # Get counts by current state
        state_counts = query(
            """SELECT ws.name as state_name, COUNT(*) as count
               FROM enrollment_states es
               JOIN workflow_states ws ON es.state_id = ws.id
               JOIN enrollments e ON es.enrollment_id = e.id
               WHERE e.program_id = ? AND e.outcome = 'active' AND es.end_date IS NULL
               GROUP BY ws.name""",
            (prog["id"],),
        )

        result.append({
            "program_id": prog["id"],
            "program_name": prog["name"],
            "active_enrollments": active_count,
            "states": {row["state_name"]: row["count"] for row in state_counts},
        })
    return result


@router.get("/{program_id}")
def get_program(program_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM programs WHERE id = ?", (program_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Program not found")
    return results[0]


@router.post("", status_code=201)
def create_program(program: ProgramCreate, user: str = Depends(require_medical_role)) -> dict:
    row_id = execute(
        "INSERT INTO programs (name, description, active) VALUES (?, ?, ?)",
        (program.name, program.description, 1 if program.active else 0),
    )
    return get_program(row_id, user)


@router.put("/{program_id}")
def update_program(program_id: int, program: ProgramUpdate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM programs WHERE id = ?", (program_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found")

    updates: list[str] = []
    params: list = []
    if program.name is not None:
        updates.append("name = ?")
        params.append(program.name)
    if program.description is not None:
        updates.append("description = ?")
        params.append(program.description)
    if program.active is not None:
        updates.append("active = ?")
        params.append(1 if program.active else 0)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(program_id)
    execute(f"UPDATE programs SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_program(program_id, user)


@router.delete("/{program_id}", status_code=204)
def delete_program(program_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM programs WHERE id = ?", (program_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found")
    execute("DELETE FROM programs WHERE id = ?", (program_id,))


@router.get("/{program_id}/enrollments")
def list_program_enrollments(
    program_id: int,
    status: Optional[str] = None,
    user: str = Depends(require_medical_role),
) -> list[dict]:
    existing = query("SELECT id FROM programs WHERE id = ?", (program_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found")

    sql = "SELECT * FROM enrollments WHERE program_id = ?"
    params: list = [program_id]
    if status:
        sql += " AND outcome = ?"
        params.append(status)
    sql += " ORDER BY enrollment_date DESC"

    enrollments = query(sql, tuple(params))
    for enrollment in enrollments:
        current = query(
            """SELECT ws.name as state_name FROM enrollment_states es
               JOIN workflow_states ws ON es.state_id = ws.id
               WHERE es.enrollment_id = ? AND es.end_date IS NULL
               ORDER BY es.start_date DESC LIMIT 1""",
            (enrollment["id"],),
        )
        enrollment["current_state"] = current[0]["state_name"] if current else None
    return enrollments
