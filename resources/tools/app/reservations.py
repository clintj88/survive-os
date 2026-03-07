"""Reservation system API routes."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


class ReservationCreate(BaseModel):
    tool_id: int
    reserved_by: str
    date_needed: str
    duration_days: int = 1
    purpose: str = ""


class ReservationUpdate(BaseModel):
    date_needed: Optional[str] = None
    duration_days: Optional[int] = None
    purpose: Optional[str] = None


def _check_conflict(tool_id: int, start: str, duration: int, exclude_id: Optional[int] = None) -> bool:
    """Check if a reservation would conflict with existing ones."""
    start_date = date.fromisoformat(start)
    end_date = (start_date + timedelta(days=duration)).isoformat()

    params: list = [tool_id, end_date, start]
    exclude_clause = ""
    if exclude_id is not None:
        exclude_clause = " AND id != ?"
        params.append(exclude_id)

    conflicts = query(
        f"""SELECT id FROM reservations
            WHERE tool_id = ? AND status = 'active'
            AND date_needed < ?
            AND date(date_needed, '+' || duration_days || ' days') > ?
            {exclude_clause}""",
        tuple(params),
    )
    return len(conflicts) > 0


@router.post("", status_code=201)
def create_reservation(req: ReservationCreate) -> dict:
    tools = query("SELECT id FROM tools WHERE id = ?", (req.tool_id,))
    if not tools:
        raise HTTPException(status_code=404, detail="Tool not found")

    if _check_conflict(req.tool_id, req.date_needed, req.duration_days):
        raise HTTPException(status_code=409, detail="Reservation conflicts with existing booking")

    res_id = execute(
        """INSERT INTO reservations (tool_id, reserved_by, date_needed, duration_days, purpose)
           VALUES (?, ?, ?, ?, ?)""",
        (req.tool_id, req.reserved_by, req.date_needed, req.duration_days, req.purpose),
    )
    results = query(
        """SELECT r.*, t.name as tool_name FROM reservations r
           JOIN tools t ON r.tool_id = t.id WHERE r.id = ?""",
        (res_id,),
    )
    return results[0]


@router.get("")
def list_reservations(
    tool_id: Optional[int] = Query(None),
    reserved_by: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> list[dict]:
    clauses: list[str] = []
    params: list = []

    if tool_id is not None:
        clauses.append("r.tool_id = ?")
        params.append(tool_id)
    if reserved_by:
        clauses.append("r.reserved_by = ?")
        params.append(reserved_by)
    if status:
        clauses.append("r.status = ?")
        params.append(status)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return query(
        f"""SELECT r.*, t.name as tool_name FROM reservations r
            JOIN tools t ON r.tool_id = t.id{where}
            ORDER BY r.date_needed""",
        tuple(params),
    )


@router.get("/upcoming")
def upcoming_reservations(days: int = Query(7, ge=1)) -> list[dict]:
    end_date = (date.today() + timedelta(days=days)).isoformat()
    today = date.today().isoformat()
    return query(
        """SELECT r.*, t.name as tool_name FROM reservations r
           JOIN tools t ON r.tool_id = t.id
           WHERE r.status = 'active' AND r.date_needed >= ? AND r.date_needed <= ?
           ORDER BY r.date_needed""",
        (today, end_date),
    )


@router.get("/queue/{tool_id}")
def reservation_queue(tool_id: int) -> list[dict]:
    today = date.today().isoformat()
    return query(
        """SELECT r.*, t.name as tool_name FROM reservations r
           JOIN tools t ON r.tool_id = t.id
           WHERE r.tool_id = ? AND r.status = 'active' AND r.date_needed >= ?
           ORDER BY r.date_needed""",
        (tool_id, today),
    )


@router.put("/{reservation_id}")
def update_reservation(reservation_id: int, req: ReservationUpdate) -> dict:
    existing = query("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Reservation not found")

    res = existing[0]
    new_date = req.date_needed or res["date_needed"]
    new_duration = req.duration_days or res["duration_days"]

    if req.date_needed or req.duration_days:
        if _check_conflict(res["tool_id"], new_date, new_duration, exclude_id=reservation_id):
            raise HTTPException(status_code=409, detail="Updated reservation conflicts")

    updates: list[str] = []
    params: list = []
    for field in ["date_needed", "duration_days", "purpose"]:
        value = getattr(req, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(reservation_id)
    execute(f"UPDATE reservations SET {', '.join(updates)} WHERE id = ?", tuple(params))
    results = query(
        """SELECT r.*, t.name as tool_name FROM reservations r
           JOIN tools t ON r.tool_id = t.id WHERE r.id = ?""",
        (reservation_id,),
    )
    return results[0]


@router.post("/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int) -> dict:
    existing = query("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Reservation not found")

    execute("UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,))
    results = query(
        """SELECT r.*, t.name as tool_name FROM reservations r
           JOIN tools t ON r.tool_id = t.id WHERE r.id = ?""",
        (reservation_id,),
    )
    return results[0]
