"""Preventive Maintenance Scheduler API routes."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from .database import execute, query

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class ItemCreate(BaseModel):
    name: str
    category: str
    location: str = ""
    install_date: Optional[str] = None
    condition: str = "good"
    notes: str = ""


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class ScheduleCreate(BaseModel):
    item_id: int
    task_description: str
    frequency_days: int
    last_performed: Optional[str] = None
    next_due: Optional[str] = None


class ScheduleUpdate(BaseModel):
    task_description: Optional[str] = None
    frequency_days: Optional[int] = None
    next_due: Optional[str] = None


@router.get("/items")
def list_items(category: Optional[str] = Query(None)) -> list[dict]:
    if category:
        return query(
            "SELECT * FROM infrastructure_items WHERE category = ? ORDER BY name",
            (category,),
        )
    return query("SELECT * FROM infrastructure_items ORDER BY name")


@router.post("/items", status_code=201)
def create_item(item: ItemCreate) -> dict:
    item_id = execute(
        """INSERT INTO infrastructure_items (name, category, location, install_date, condition, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (item.name, item.category, item.location, item.install_date, item.condition, item.notes),
    )
    results = query("SELECT * FROM infrastructure_items WHERE id = ?", (item_id,))
    return results[0]


@router.get("/items/{item_id}")
def get_item(item_id: int) -> dict:
    results = query("SELECT * FROM infrastructure_items WHERE id = ?", (item_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")
    return results[0]


@router.put("/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate) -> dict:
    existing = query("SELECT id FROM infrastructure_items WHERE id = ?", (item_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "category", "location", "condition", "notes"]:
        value = getattr(item, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(item_id)
    execute(f"UPDATE infrastructure_items SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_item(item_id)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    existing = query("SELECT id FROM infrastructure_items WHERE id = ?", (item_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    execute("DELETE FROM maintenance_history WHERE item_id = ?", (item_id,))
    execute("DELETE FROM maintenance_schedules WHERE item_id = ?", (item_id,))
    execute("DELETE FROM infrastructure_items WHERE id = ?", (item_id,))


@router.get("/schedules")
def list_schedules(item_id: Optional[int] = Query(None)) -> list[dict]:
    if item_id is not None:
        return query(
            """SELECT s.*, i.name as item_name FROM maintenance_schedules s
               JOIN infrastructure_items i ON s.item_id = i.id
               WHERE s.item_id = ? ORDER BY s.next_due""",
            (item_id,),
        )
    return query(
        """SELECT s.*, i.name as item_name FROM maintenance_schedules s
           JOIN infrastructure_items i ON s.item_id = i.id
           ORDER BY s.next_due"""
    )


@router.post("/schedules", status_code=201)
def create_schedule(schedule: ScheduleCreate) -> dict:
    items = query("SELECT id FROM infrastructure_items WHERE id = ?", (schedule.item_id,))
    if not items:
        raise HTTPException(status_code=400, detail="Item not found")

    next_due = schedule.next_due
    if not next_due:
        next_due = (date.today() + timedelta(days=schedule.frequency_days)).isoformat()

    sched_id = execute(
        """INSERT INTO maintenance_schedules (item_id, task_description, frequency_days, last_performed, next_due)
           VALUES (?, ?, ?, ?, ?)""",
        (schedule.item_id, schedule.task_description, schedule.frequency_days, schedule.last_performed, next_due),
    )
    results = query(
        """SELECT s.*, i.name as item_name FROM maintenance_schedules s
           JOIN infrastructure_items i ON s.item_id = i.id WHERE s.id = ?""",
        (sched_id,),
    )
    return results[0]


@router.put("/schedules/{schedule_id}")
def update_schedule(schedule_id: int, schedule: ScheduleUpdate) -> dict:
    existing = query("SELECT id FROM maintenance_schedules WHERE id = ?", (schedule_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    updates: list[str] = []
    params: list = []
    for field in ["task_description", "frequency_days", "next_due"]:
        value = getattr(schedule, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(schedule_id)
    execute(f"UPDATE maintenance_schedules SET {', '.join(updates)} WHERE id = ?", tuple(params))
    results = query(
        """SELECT s.*, i.name as item_name FROM maintenance_schedules s
           JOIN infrastructure_items i ON s.item_id = i.id WHERE s.id = ?""",
        (schedule_id,),
    )
    return results[0]


@router.get("/overdue")
def list_overdue() -> list[dict]:
    today = date.today().isoformat()
    return query(
        """SELECT s.*, i.name as item_name FROM maintenance_schedules s
           JOIN infrastructure_items i ON s.item_id = i.id
           WHERE s.next_due < ? ORDER BY s.next_due""",
        (today,),
    )


class CompleteRequest(BaseModel):
    performed_by: str = ""
    notes: str = ""


@router.post("/schedules/{schedule_id}/complete")
def complete_maintenance(schedule_id: int, req: CompleteRequest) -> dict:
    schedules = query("SELECT * FROM maintenance_schedules WHERE id = ?", (schedule_id,))
    if not schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")

    sched = schedules[0]
    now = datetime.now(timezone.utc).isoformat()

    execute(
        """INSERT INTO maintenance_history (schedule_id, item_id, performed_at, performed_by, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (schedule_id, sched["item_id"], now, req.performed_by, req.notes),
    )

    next_due = (date.today() + timedelta(days=sched["frequency_days"])).isoformat()
    execute(
        "UPDATE maintenance_schedules SET last_performed = ?, next_due = ? WHERE id = ?",
        (now, next_due, schedule_id),
    )

    results = query(
        """SELECT s.*, i.name as item_name FROM maintenance_schedules s
           JOIN infrastructure_items i ON s.item_id = i.id WHERE s.id = ?""",
        (schedule_id,),
    )
    return results[0]


@router.get("/history")
def list_history(item_id: Optional[int] = Query(None)) -> list[dict]:
    if item_id is not None:
        return query(
            """SELECT h.*, s.task_description FROM maintenance_history h
               JOIN maintenance_schedules s ON h.schedule_id = s.id
               WHERE h.item_id = ? ORDER BY h.performed_at DESC""",
            (item_id,),
        )
    return query(
        """SELECT h.*, s.task_description FROM maintenance_history h
           JOIN maintenance_schedules s ON h.schedule_id = s.id
           ORDER BY h.performed_at DESC"""
    )
