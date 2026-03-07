"""Treaties & Agreements routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/treaties", tags=["treaties"])


class TreatyCreate(BaseModel):
    title: str
    parties: str = ""
    content: str = ""
    status: str = "draft"
    effective_date: Optional[str] = None


class TreatyUpdate(BaseModel):
    title: Optional[str] = None
    parties: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[str] = None
    changed_by: str = ""


class SignatoryAdd(BaseModel):
    person_name: str


@router.get("")
def list_treaties() -> list[dict]:
    return query("SELECT * FROM treaties ORDER BY created_at DESC")


@router.get("/{treaty_id}")
def get_treaty(treaty_id: int) -> dict:
    results = query("SELECT * FROM treaties WHERE id = ?", (treaty_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Treaty not found")
    treaty = results[0]
    treaty["signatories"] = query(
        "SELECT person_name, signed_at FROM treaty_signatories WHERE treaty_id = ? ORDER BY signed_at",
        (treaty_id,),
    )
    treaty["versions"] = query(
        "SELECT version_num, changed_by, changed_at FROM treaty_versions WHERE treaty_id = ? ORDER BY version_num",
        (treaty_id,),
    )
    return treaty


@router.post("", status_code=201)
def create_treaty(treaty: TreatyCreate) -> dict:
    tid = execute(
        """INSERT INTO treaties (title, parties, content, status, effective_date)
           VALUES (?, ?, ?, ?, ?)""",
        (treaty.title, treaty.parties, treaty.content, treaty.status, treaty.effective_date),
    )
    # Save initial version
    execute(
        "INSERT INTO treaty_versions (treaty_id, version_num, content, changed_by) VALUES (?, 1, ?, ?)",
        (tid, treaty.content, "creator"),
    )
    return get_treaty(tid)


@router.put("/{treaty_id}")
def update_treaty(treaty_id: int, update: TreatyUpdate) -> dict:
    existing = query("SELECT * FROM treaties WHERE id = ?", (treaty_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Treaty not found")
    updates: list[str] = []
    params: list = []
    for field in ("title", "parties", "content", "status", "effective_date"):
        val = getattr(update, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = datetime('now')")
    params.append(treaty_id)
    execute(f"UPDATE treaties SET {', '.join(updates)} WHERE id = ?", tuple(params))
    # Track version if content changed
    if update.content is not None:
        max_ver = query(
            "SELECT COALESCE(MAX(version_num), 0) as v FROM treaty_versions WHERE treaty_id = ?",
            (treaty_id,),
        )[0]["v"]
        execute(
            "INSERT INTO treaty_versions (treaty_id, version_num, content, changed_by) VALUES (?, ?, ?, ?)",
            (treaty_id, max_ver + 1, update.content, update.changed_by),
        )
    return get_treaty(treaty_id)


@router.post("/{treaty_id}/signatories", status_code=201)
def add_signatory(treaty_id: int, sig: SignatoryAdd) -> dict:
    existing = query("SELECT id FROM treaties WHERE id = ?", (treaty_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Treaty not found")
    execute(
        "INSERT INTO treaty_signatories (treaty_id, person_name) VALUES (?, ?)",
        (treaty_id, sig.person_name),
    )
    return get_treaty(treaty_id)


@router.get("/{treaty_id}/versions")
def get_versions(treaty_id: int) -> list[dict]:
    return query(
        "SELECT * FROM treaty_versions WHERE treaty_id = ? ORDER BY version_num",
        (treaty_id,),
    )
