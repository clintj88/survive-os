"""Dispute Resolution routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


class DisputeCreate(BaseModel):
    parties: str
    description: str
    category: str = "governance"


class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    outcome: Optional[str] = None
    precedent_id: Optional[int] = None


@router.get("")
def list_disputes(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM disputes WHERE 1=1"
    params: list = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY filed_date DESC"
    return query(sql, tuple(params))


@router.get("/{dispute_id}")
def get_dispute(dispute_id: int) -> dict:
    results = query("SELECT * FROM disputes WHERE id = ?", (dispute_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute = results[0]
    if dispute["precedent_id"]:
        precedent = query("SELECT id, parties, description, outcome FROM disputes WHERE id = ?", (dispute["precedent_id"],))
        dispute["precedent"] = precedent[0] if precedent else None
    return dispute


@router.post("", status_code=201)
def create_dispute(dispute: DisputeCreate) -> dict:
    did = execute(
        "INSERT INTO disputes (parties, description, category) VALUES (?, ?, ?)",
        (dispute.parties, dispute.description, dispute.category),
    )
    return get_dispute(did)


@router.put("/{dispute_id}")
def update_dispute(dispute_id: int, update: DisputeUpdate) -> dict:
    existing = query("SELECT id FROM disputes WHERE id = ?", (dispute_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Dispute not found")
    updates: list[str] = []
    params: list = []
    for field in ("status", "resolution_notes", "outcome", "precedent_id"):
        val = getattr(update, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(dispute_id)
    execute(f"UPDATE disputes SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_dispute(dispute_id)
