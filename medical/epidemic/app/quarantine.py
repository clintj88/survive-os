"""Quarantine management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/quarantine", tags=["quarantine"])


class QuarantineCreate(BaseModel):
    person: str
    start_date: str
    expected_end: str
    location: str = ""
    reason: str = ""


class QuarantineUpdate(BaseModel):
    expected_end: Optional[str] = None
    location: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class CheckinCreate(BaseModel):
    date: str
    temperature: Optional[float] = None
    symptoms: str = ""
    notes: str = ""


class SupplyCreate(BaseModel):
    item: str
    quantity: int = 1
    status: str = "needed"


@router.get("")
def list_quarantines(
    status: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    if status:
        return query(
            "SELECT * FROM quarantines WHERE status = ? ORDER BY start_date DESC",
            (status,),
        )
    return query("SELECT * FROM quarantines ORDER BY start_date DESC")


@router.get("/census")
def quarantine_census(_: str = Depends(require_medical_role)) -> dict:
    """Get quarantine census summary."""
    active = query("SELECT COUNT(*) as count FROM quarantines WHERE status = 'active'")
    completed = query("SELECT COUNT(*) as count FROM quarantines WHERE status = 'completed'")
    released = query("SELECT COUNT(*) as count FROM quarantines WHERE status = 'released'")
    supplies_needed = query(
        "SELECT COUNT(*) as count FROM quarantine_supplies WHERE status = 'needed'"
    )
    return {
        "active": active[0]["count"] if active else 0,
        "completed": completed[0]["count"] if completed else 0,
        "released": released[0]["count"] if released else 0,
        "supplies_needed": supplies_needed[0]["count"] if supplies_needed else 0,
    }


@router.get("/{quarantine_id}")
def get_quarantine(quarantine_id: int, _: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM quarantines WHERE id = ?", (quarantine_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Quarantine record not found")
    return results[0]


@router.post("", status_code=201)
def create_quarantine(
    q: QuarantineCreate, _: str = Depends(require_medical_role)
) -> dict:
    qid = execute(
        """INSERT INTO quarantines (person, start_date, expected_end, location, reason)
           VALUES (?, ?, ?, ?, ?)""",
        (q.person, q.start_date, q.expected_end, q.location, q.reason),
    )
    return get_quarantine(qid)


@router.put("/{quarantine_id}")
def update_quarantine(
    quarantine_id: int, q: QuarantineUpdate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM quarantines WHERE id = ?", (quarantine_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Quarantine record not found")

    updates: list[str] = []
    params: list = []
    for field in ("expected_end", "location", "reason", "status"):
        value = getattr(q, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if q.status and q.status not in ("active", "completed", "released"):
        raise HTTPException(
            status_code=400,
            detail="Status must be 'active', 'completed', or 'released'",
        )

    params.append(quarantine_id)
    execute(f"UPDATE quarantines SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_quarantine(quarantine_id)


# --- Check-ins ---

@router.get("/{quarantine_id}/checkins")
def list_checkins(
    quarantine_id: int, _: str = Depends(require_medical_role)
) -> list[dict]:
    existing = query("SELECT id FROM quarantines WHERE id = ?", (quarantine_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Quarantine record not found")
    return query(
        "SELECT * FROM quarantine_checkins WHERE quarantine_id = ? ORDER BY date DESC",
        (quarantine_id,),
    )


@router.post("/{quarantine_id}/checkins", status_code=201)
def create_checkin(
    quarantine_id: int, checkin: CheckinCreate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM quarantines WHERE id = ?", (quarantine_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Quarantine record not found")

    cid = execute(
        """INSERT INTO quarantine_checkins (quarantine_id, date, temperature, symptoms, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (quarantine_id, checkin.date, checkin.temperature, checkin.symptoms, checkin.notes),
    )
    results = query("SELECT * FROM quarantine_checkins WHERE id = ?", (cid,))
    return results[0]


# --- Supplies ---

@router.get("/{quarantine_id}/supplies")
def list_supplies(
    quarantine_id: int, _: str = Depends(require_medical_role)
) -> list[dict]:
    existing = query("SELECT id FROM quarantines WHERE id = ?", (quarantine_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Quarantine record not found")
    return query(
        "SELECT * FROM quarantine_supplies WHERE quarantine_id = ? ORDER BY created_at DESC",
        (quarantine_id,),
    )


@router.post("/{quarantine_id}/supplies", status_code=201)
def create_supply(
    quarantine_id: int, supply: SupplyCreate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM quarantines WHERE id = ?", (quarantine_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Quarantine record not found")

    sid = execute(
        """INSERT INTO quarantine_supplies (quarantine_id, item, quantity, status)
           VALUES (?, ?, ?, ?)""",
        (quarantine_id, supply.item, supply.quantity, supply.status),
    )
    results = query("SELECT * FROM quarantine_supplies WHERE id = ?", (sid,))
    return results[0]


@router.put("/{quarantine_id}/supplies/{supply_id}")
def update_supply_status(
    quarantine_id: int,
    supply_id: int,
    status: str = Query(...),
    _: str = Depends(require_medical_role),
) -> dict:
    results = query(
        "SELECT * FROM quarantine_supplies WHERE id = ? AND quarantine_id = ?",
        (supply_id, quarantine_id),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Supply not found")

    if status not in ("needed", "delivered", "consumed"):
        raise HTTPException(
            status_code=400,
            detail="Status must be 'needed', 'delivered', or 'consumed'",
        )

    execute("UPDATE quarantine_supplies SET status = ? WHERE id = ?", (status, supply_id))
    results = query("SELECT * FROM quarantine_supplies WHERE id = ?", (supply_id,))
    return results[0]
