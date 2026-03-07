"""Tool inventory CRUD API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolCreate(BaseModel):
    name: str
    category: str
    description: str = ""
    condition: str = "good"
    location: str = ""
    acquired_date: Optional[str] = None
    value_estimate: Optional[float] = None
    photo_path: Optional[str] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    value_estimate: Optional[float] = None
    photo_path: Optional[str] = None


@router.get("")
def list_tools(
    category: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> list[dict]:
    clauses: list[str] = []
    params: list = []

    if category:
        clauses.append("category = ?")
        params.append(category)
    if condition:
        clauses.append("condition = ?")
        params.append(condition)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if search:
        clauses.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return query(f"SELECT * FROM tools{where} ORDER BY name", tuple(params))


@router.post("", status_code=201)
def create_tool(tool: ToolCreate) -> dict:
    tool_id = execute(
        """INSERT INTO tools (name, category, description, condition, location,
           acquired_date, value_estimate, photo_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (tool.name, tool.category, tool.description, tool.condition,
         tool.location, tool.acquired_date, tool.value_estimate, tool.photo_path),
    )
    results = query("SELECT * FROM tools WHERE id = ?", (tool_id,))
    return results[0]


@router.get("/{tool_id}")
def get_tool(tool_id: int) -> dict:
    results = query("SELECT * FROM tools WHERE id = ?", (tool_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Tool not found")
    return results[0]


@router.put("/{tool_id}")
def update_tool(tool_id: int, tool: ToolUpdate) -> dict:
    existing = query("SELECT id FROM tools WHERE id = ?", (tool_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Tool not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "category", "description", "condition", "status",
                  "location", "value_estimate", "photo_path"]:
        value = getattr(tool, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(tool_id)
    execute(f"UPDATE tools SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_tool(tool_id)


@router.delete("/{tool_id}", status_code=204)
def delete_tool(tool_id: int) -> None:
    existing = query("SELECT id FROM tools WHERE id = ?", (tool_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Tool not found")
    execute("DELETE FROM reservations WHERE tool_id = ?", (tool_id,))
    execute("DELETE FROM maintenance_history WHERE tool_id = ?", (tool_id,))
    execute("DELETE FROM maintenance_tasks WHERE tool_id = ?", (tool_id,))
    execute("DELETE FROM checkouts WHERE tool_id = ?", (tool_id,))
    execute("DELETE FROM tools WHERE id = ?", (tool_id,))
