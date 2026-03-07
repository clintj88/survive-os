"""Patient enrollment and state transition endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, get_connection, query

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])


class EnrollmentCreate(BaseModel):
    patient_id: str
    program_id: int
    enrolled_by: str
    enrollment_date: Optional[str] = None


class StateTransition(BaseModel):
    to_state_id: int
    changed_by: str
    reason: str = ""


class EnrollmentComplete(BaseModel):
    outcome: str
    changed_by: str
    reason: str = ""


@router.get("")
def list_enrollments(
    patient_id: Optional[str] = None,
    outcome: Optional[str] = None,
    user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = "SELECT * FROM enrollments WHERE 1=1"
    params: list = []
    if patient_id:
        sql += " AND patient_id = ?"
        params.append(patient_id)
    if outcome:
        sql += " AND outcome = ?"
        params.append(outcome)
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


@router.get("/{enrollment_id}")
def get_enrollment(enrollment_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment = results[0]
    current = query(
        """SELECT ws.name as state_name, ws.id as state_id FROM enrollment_states es
           JOIN workflow_states ws ON es.state_id = ws.id
           WHERE es.enrollment_id = ? AND es.end_date IS NULL
           ORDER BY es.start_date DESC LIMIT 1""",
        (enrollment_id,),
    )
    enrollment["current_state"] = current[0]["state_name"] if current else None
    enrollment["current_state_id"] = current[0]["state_id"] if current else None
    return enrollment


@router.post("", status_code=201)
def create_enrollment(enrollment: EnrollmentCreate, user: str = Depends(require_medical_role)) -> dict:
    prog = query("SELECT id FROM programs WHERE id = ? AND active = 1", (enrollment.program_id,))
    if not prog:
        raise HTTPException(status_code=404, detail="Active program not found")

    # Find the workflow and initial state
    workflows = query(
        "SELECT id FROM program_workflows WHERE program_id = ? LIMIT 1",
        (enrollment.program_id,),
    )
    if not workflows:
        raise HTTPException(status_code=400, detail="Program has no workflow defined")

    initial_states = query(
        "SELECT id FROM workflow_states WHERE workflow_id = ? AND initial = 1 LIMIT 1",
        (workflows[0]["id"],),
    )
    if not initial_states:
        raise HTTPException(status_code=400, detail="Workflow has no initial state")

    enrollment_date = enrollment.enrollment_date or datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO enrollments (patient_id, program_id, enrolled_by, enrollment_date)
               VALUES (?, ?, ?, ?)""",
            (enrollment.patient_id, enrollment.program_id, enrollment.enrolled_by, enrollment_date),
        )
        enrollment_id = cursor.lastrowid

        conn.execute(
            """INSERT INTO enrollment_states (enrollment_id, state_id, start_date, changed_by, reason)
               VALUES (?, ?, ?, ?, ?)""",
            (enrollment_id, initial_states[0]["id"], enrollment_date, enrollment.enrolled_by, "Initial enrollment"),
        )
        conn.commit()
    finally:
        conn.close()

    return get_enrollment(enrollment_id, user)


@router.post("/{enrollment_id}/transition")
def transition_state(
    enrollment_id: int,
    transition: StateTransition,
    user: str = Depends(require_medical_role),
) -> dict:
    enrollment = query("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment[0]["outcome"] != "active":
        raise HTTPException(status_code=400, detail="Enrollment is not active")

    # Get current state
    current = query(
        """SELECT es.id, es.state_id FROM enrollment_states es
           WHERE es.enrollment_id = ? AND es.end_date IS NULL
           ORDER BY es.start_date DESC LIMIT 1""",
        (enrollment_id,),
    )
    if not current:
        raise HTTPException(status_code=400, detail="No current state found")

    current_state_id = current[0]["state_id"]

    # Validate transition is allowed
    allowed = query(
        "SELECT id FROM state_transitions WHERE from_state_id = ? AND to_state_id = ?",
        (current_state_id, transition.to_state_id),
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="Transition not allowed")

    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        # End current state
        conn.execute(
            "UPDATE enrollment_states SET end_date = ? WHERE id = ?",
            (now, current[0]["id"]),
        )
        # Start new state
        conn.execute(
            """INSERT INTO enrollment_states (enrollment_id, state_id, start_date, changed_by, reason)
               VALUES (?, ?, ?, ?, ?)""",
            (enrollment_id, transition.to_state_id, now, transition.changed_by, transition.reason),
        )
        # If new state is terminal, complete enrollment
        terminal = query(
            "SELECT terminal FROM workflow_states WHERE id = ?",
            (transition.to_state_id,),
        )
        if terminal and terminal[0]["terminal"]:
            state_name = query(
                "SELECT name FROM workflow_states WHERE id = ?",
                (transition.to_state_id,),
            )[0]["name"]
            conn.execute(
                "UPDATE enrollments SET outcome = 'completed', completion_date = ?, updated_at = ? WHERE id = ?",
                (now, now, enrollment_id),
            )
        else:
            conn.execute(
                "UPDATE enrollments SET updated_at = ? WHERE id = ?",
                (now, enrollment_id),
            )
        conn.commit()
    finally:
        conn.close()

    return get_enrollment(enrollment_id, user)


@router.get("/{enrollment_id}/history")
def enrollment_history(enrollment_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    existing = query("SELECT id FROM enrollments WHERE id = ?", (enrollment_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return query(
        """SELECT es.*, ws.name as state_name
           FROM enrollment_states es
           JOIN workflow_states ws ON es.state_id = ws.id
           WHERE es.enrollment_id = ?
           ORDER BY es.start_date""",
        (enrollment_id,),
    )


@router.post("/{enrollment_id}/complete")
def complete_enrollment(
    enrollment_id: int,
    data: EnrollmentComplete,
    user: str = Depends(require_medical_role),
) -> dict:
    enrollment = query("SELECT * FROM enrollments WHERE id = ?", (enrollment_id,))
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if enrollment[0]["outcome"] != "active":
        raise HTTPException(status_code=400, detail="Enrollment is not active")

    valid_outcomes = ("completed", "defaulted", "transferred_out", "died")
    if data.outcome not in valid_outcomes:
        raise HTTPException(status_code=400, detail=f"Invalid outcome. Must be one of: {', '.join(valid_outcomes)}")

    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        # End current state
        conn.execute(
            "UPDATE enrollment_states SET end_date = ? WHERE enrollment_id = ? AND end_date IS NULL",
            (now, enrollment_id),
        )
        conn.execute(
            "UPDATE enrollments SET outcome = ?, completion_date = ?, updated_at = ? WHERE id = ?",
            (data.outcome, now, now, enrollment_id),
        )
        conn.commit()
    finally:
        conn.close()

    return get_enrollment(enrollment_id, user)
