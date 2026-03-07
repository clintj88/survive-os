"""Maintenance scheduling API routes."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class TaskCreate(BaseModel):
    tool_id: int
    task: str
    frequency_days: int
    last_performed: Optional[str] = None
    next_due: Optional[str] = None


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    frequency_days: Optional[int] = None
    next_due: Optional[str] = None


class HistoryCreate(BaseModel):
    tool_id: int
    task: str
    performed_by: str = ""
    notes: str = ""
    parts_used: str = ""


class CompleteRequest(BaseModel):
    performed_by: str = ""
    notes: str = ""
    parts_used: str = ""


@router.get("/tasks")
def list_tasks(tool_id: Optional[int] = Query(None)) -> list[dict]:
    if tool_id is not None:
        return query(
            """SELECT mt.*, t.name as tool_name FROM maintenance_tasks mt
               JOIN tools t ON mt.tool_id = t.id
               WHERE mt.tool_id = ? ORDER BY mt.next_due""",
            (tool_id,),
        )
    return query(
        """SELECT mt.*, t.name as tool_name FROM maintenance_tasks mt
           JOIN tools t ON mt.tool_id = t.id ORDER BY mt.next_due"""
    )


@router.post("/tasks", status_code=201)
def create_task(task: TaskCreate) -> dict:
    tools = query("SELECT id FROM tools WHERE id = ?", (task.tool_id,))
    if not tools:
        raise HTTPException(status_code=400, detail="Tool not found")

    next_due = task.next_due
    if not next_due:
        next_due = (date.today() + timedelta(days=task.frequency_days)).isoformat()

    task_id = execute(
        """INSERT INTO maintenance_tasks (tool_id, task, frequency_days, last_performed, next_due)
           VALUES (?, ?, ?, ?, ?)""",
        (task.tool_id, task.task, task.frequency_days, task.last_performed, next_due),
    )
    results = query(
        """SELECT mt.*, t.name as tool_name FROM maintenance_tasks mt
           JOIN tools t ON mt.tool_id = t.id WHERE mt.id = ?""",
        (task_id,),
    )
    return results[0]


@router.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate) -> dict:
    existing = query("SELECT id FROM maintenance_tasks WHERE id = ?", (task_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    updates: list[str] = []
    params: list = []
    for field in ["task", "frequency_days", "next_due"]:
        value = getattr(task, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(task_id)
    execute(f"UPDATE maintenance_tasks SET {', '.join(updates)} WHERE id = ?", tuple(params))
    results = query(
        """SELECT mt.*, t.name as tool_name FROM maintenance_tasks mt
           JOIN tools t ON mt.tool_id = t.id WHERE mt.id = ?""",
        (task_id,),
    )
    return results[0]


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> None:
    existing = query("SELECT id FROM maintenance_tasks WHERE id = ?", (task_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    execute("DELETE FROM maintenance_tasks WHERE id = ?", (task_id,))


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, req: CompleteRequest) -> dict:
    tasks = query("SELECT * FROM maintenance_tasks WHERE id = ?", (task_id,))
    if not tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    mt = tasks[0]
    now = date.today().isoformat()

    execute(
        """INSERT INTO maintenance_history (tool_id, task, performed_by, performed_date, notes, parts_used)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (mt["tool_id"], mt["task"], req.performed_by, now, req.notes, req.parts_used),
    )

    next_due = (date.today() + timedelta(days=mt["frequency_days"])).isoformat()
    execute(
        "UPDATE maintenance_tasks SET last_performed = ?, next_due = ? WHERE id = ?",
        (now, next_due, task_id),
    )

    results = query(
        """SELECT mt.*, t.name as tool_name FROM maintenance_tasks mt
           JOIN tools t ON mt.tool_id = t.id WHERE mt.id = ?""",
        (task_id,),
    )
    return results[0]


@router.get("/overdue")
def list_overdue() -> list[dict]:
    today = date.today().isoformat()
    return query(
        """SELECT mt.*, t.name as tool_name, t.condition as tool_condition
           FROM maintenance_tasks mt
           JOIN tools t ON mt.tool_id = t.id
           WHERE mt.next_due < ? ORDER BY mt.next_due""",
        (today,),
    )


@router.get("/history")
def list_history(tool_id: Optional[int] = Query(None)) -> list[dict]:
    if tool_id is not None:
        return query(
            """SELECT * FROM maintenance_history
               WHERE tool_id = ? ORDER BY performed_date DESC""",
            (tool_id,),
        )
    return query("SELECT * FROM maintenance_history ORDER BY performed_date DESC")


@router.get("/condition-alerts")
def condition_alerts() -> list[dict]:
    """Suggest condition downgrades for tools with overdue maintenance."""
    today = date.today().isoformat()
    return query(
        """SELECT t.id as tool_id, t.name, t.condition,
                  COUNT(mt.id) as overdue_tasks,
                  MIN(mt.next_due) as oldest_overdue
           FROM tools t
           JOIN maintenance_tasks mt ON t.id = mt.tool_id
           WHERE mt.next_due < ? AND t.condition IN ('excellent', 'good', 'fair')
           GROUP BY t.id
           ORDER BY overdue_tasks DESC""",
        (today,),
    )
