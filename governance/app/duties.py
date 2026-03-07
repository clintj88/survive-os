"""Duty Scheduling routes."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/duties", tags=["duties"])


class DutyAssign(BaseModel):
    person_id: int
    duty_type: str
    duty_date: str
    shift: str = "morning"


class SwapRequest(BaseModel):
    assignment_id: int
    requester_id: int
    target_id: int


@router.get("/assignments")
def list_assignments(
    duty_date: Optional[str] = Query(None),
    person_id: Optional[int] = Query(None),
    duty_type: Optional[str] = Query(None),
) -> list[dict]:
    sql = """SELECT da.*, p.name as person_name
             FROM duty_assignments da JOIN persons p ON da.person_id = p.id
             WHERE 1=1"""
    params: list = []
    if duty_date:
        sql += " AND da.duty_date = ?"
        params.append(duty_date)
    if person_id:
        sql += " AND da.person_id = ?"
        params.append(person_id)
    if duty_type:
        sql += " AND da.duty_type = ?"
        params.append(duty_type)
    sql += " ORDER BY da.duty_date, da.shift"
    return query(sql, tuple(params))


@router.post("/assignments", status_code=201)
def create_assignment(duty: DutyAssign) -> dict:
    person = query("SELECT id FROM persons WHERE id = ?", (duty.person_id,))
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    aid = execute(
        "INSERT INTO duty_assignments (person_id, duty_type, duty_date, shift) VALUES (?, ?, ?, ?)",
        (duty.person_id, duty.duty_type, duty.duty_date, duty.shift),
    )
    return query(
        "SELECT da.*, p.name as person_name FROM duty_assignments da JOIN persons p ON da.person_id = p.id WHERE da.id = ?",
        (aid,),
    )[0]


@router.get("/fairness")
def fairness_report() -> list[dict]:
    return query(
        """SELECT p.id, p.name, da.duty_type, COUNT(*) as duty_count
           FROM duty_assignments da JOIN persons p ON da.person_id = p.id
           GROUP BY p.id, da.duty_type
           ORDER BY duty_count DESC"""
    )


@router.post("/swap-requests", status_code=201)
def create_swap_request(swap: SwapRequest) -> dict:
    assignment = query("SELECT * FROM duty_assignments WHERE id = ?", (swap.assignment_id,))
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    sid = execute(
        "INSERT INTO duty_swap_requests (assignment_id, requester_id, target_id) VALUES (?, ?, ?)",
        (swap.assignment_id, swap.requester_id, swap.target_id),
    )
    return {"id": sid, **swap.model_dump(), "status": "pending"}


@router.put("/swap-requests/{request_id}/approve")
def approve_swap(request_id: int) -> dict:
    req = query("SELECT * FROM duty_swap_requests WHERE id = ?", (request_id,))
    if not req:
        raise HTTPException(status_code=404, detail="Swap request not found")
    r = req[0]
    if r["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    execute(
        "UPDATE duty_assignments SET person_id = ?, status = 'swapped' WHERE id = ?",
        (r["target_id"], r["assignment_id"]),
    )
    execute(
        "UPDATE duty_swap_requests SET status = 'approved' WHERE id = ?",
        (request_id,),
    )
    return {"id": request_id, "status": "approved"}


@router.post("/generate-weekly")
def generate_weekly_schedule(start_date: str, duty_type: str) -> list[dict]:
    persons = query("SELECT id FROM persons WHERE status = 'active' ORDER BY id")
    if not persons:
        raise HTTPException(status_code=400, detail="No active persons")
    shifts = ["morning", "afternoon", "night"]
    assignments = []
    d = date.fromisoformat(start_date)
    person_idx = 0
    for day_offset in range(7):
        current_date = (d + timedelta(days=day_offset)).isoformat()
        for shift in shifts:
            person = persons[person_idx % len(persons)]
            existing = query(
                "SELECT id FROM duty_assignments WHERE person_id = ? AND duty_date = ? AND shift = ?",
                (person["id"], current_date, shift),
            )
            if not existing:
                aid = execute(
                    "INSERT INTO duty_assignments (person_id, duty_type, duty_date, shift) VALUES (?, ?, ?, ?)",
                    (person["id"], duty_type, current_date, shift),
                )
                assignments.append({"id": aid, "person_id": person["id"], "duty_date": current_date, "shift": shift})
            person_idx += 1
    return assignments
