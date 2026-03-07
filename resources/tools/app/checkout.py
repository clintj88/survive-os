"""Check-in/check-out system API routes."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/checkouts", tags=["checkouts"])


class CheckoutCreate(BaseModel):
    tool_id: int
    borrowed_by: str
    expected_return_date: str
    notes: str = ""


class CheckinRequest(BaseModel):
    condition_at_return: str = "good"
    notes: str = ""


@router.post("", status_code=201)
def checkout_tool(req: CheckoutCreate) -> dict:
    tools = query("SELECT * FROM tools WHERE id = ?", (req.tool_id,))
    if not tools:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool = tools[0]
    if tool["status"] != "available":
        raise HTTPException(status_code=409, detail=f"Tool is currently {tool['status']}")

    checkout_id = execute(
        """INSERT INTO checkouts (tool_id, borrowed_by, expected_return_date,
           condition_at_checkout, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (req.tool_id, req.borrowed_by, req.expected_return_date,
         tool["condition"], req.notes),
    )
    execute("UPDATE tools SET status = 'checked_out' WHERE id = ?", (req.tool_id,))

    results = query(
        """SELECT c.*, t.name as tool_name FROM checkouts c
           JOIN tools t ON c.tool_id = t.id WHERE c.id = ?""",
        (checkout_id,),
    )
    return results[0]


@router.post("/{checkout_id}/checkin")
def checkin_tool(checkout_id: int, req: CheckinRequest) -> dict:
    checkouts = query("SELECT * FROM checkouts WHERE id = ?", (checkout_id,))
    if not checkouts:
        raise HTTPException(status_code=404, detail="Checkout record not found")

    checkout = checkouts[0]
    if checkout["actual_return_date"] is not None:
        raise HTTPException(status_code=409, detail="Tool already returned")

    now = date.today().isoformat()
    execute(
        """UPDATE checkouts SET actual_return_date = ?, condition_at_return = ?,
           notes = CASE WHEN ? != '' THEN ? ELSE notes END
           WHERE id = ?""",
        (now, req.condition_at_return, req.notes, req.notes, checkout_id),
    )
    execute("UPDATE tools SET status = 'available', condition = ? WHERE id = ?",
            (req.condition_at_return, checkout["tool_id"]))

    results = query(
        """SELECT c.*, t.name as tool_name FROM checkouts c
           JOIN tools t ON c.tool_id = t.id WHERE c.id = ?""",
        (checkout_id,),
    )
    return results[0]


@router.get("")
def list_checkouts(
    tool_id: Optional[int] = Query(None),
    borrowed_by: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
) -> list[dict]:
    clauses: list[str] = []
    params: list = []

    if tool_id is not None:
        clauses.append("c.tool_id = ?")
        params.append(tool_id)
    if borrowed_by:
        clauses.append("c.borrowed_by = ?")
        params.append(borrowed_by)
    if active is True:
        clauses.append("c.actual_return_date IS NULL")
    elif active is False:
        clauses.append("c.actual_return_date IS NOT NULL")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return query(
        f"""SELECT c.*, t.name as tool_name FROM checkouts c
            JOIN tools t ON c.tool_id = t.id{where}
            ORDER BY c.checkout_date DESC""",
        tuple(params),
    )


@router.get("/overdue")
def list_overdue() -> list[dict]:
    today = date.today().isoformat()
    return query(
        """SELECT c.*, t.name as tool_name FROM checkouts c
           JOIN tools t ON c.tool_id = t.id
           WHERE c.actual_return_date IS NULL AND c.expected_return_date < ?
           ORDER BY c.expected_return_date""",
        (today,),
    )


@router.get("/by-person/{person}")
def checkouts_by_person(person: str) -> list[dict]:
    return query(
        """SELECT c.*, t.name as tool_name FROM checkouts c
           JOIN tools t ON c.tool_id = t.id
           WHERE c.borrowed_by = ? AND c.actual_return_date IS NULL
           ORDER BY c.expected_return_date""",
        (person,),
    )
