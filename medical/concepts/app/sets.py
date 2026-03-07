"""Concept set CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/sets", tags=["sets"])


class SetCreate(BaseModel):
    name: str
    description: str = ""


class SetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MemberCreate(BaseModel):
    concept_id: int
    sort_order: int = 0


@router.get("")
def list_sets(user: str = Depends(require_medical_role)) -> list[dict]:
    return query("SELECT * FROM concept_sets ORDER BY name")


@router.get("/{set_id}")
def get_set(set_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM concept_sets WHERE id = ?", (set_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Concept set not found")
    concept_set = results[0]
    concept_set["members"] = query(
        """SELECT csm.*, c.name as concept_name, c.datatype, c.concept_class
           FROM concept_set_members csm
           JOIN concepts c ON csm.concept_id = c.id
           WHERE csm.set_id = ?
           ORDER BY csm.sort_order""",
        (set_id,),
    )
    return concept_set


@router.post("", status_code=201)
def create_set(concept_set: SetCreate, user: str = Depends(require_medical_role)) -> dict:
    row_id = execute(
        "INSERT INTO concept_sets (name, description) VALUES (?, ?)",
        (concept_set.name, concept_set.description),
    )
    return get_set(row_id, user)


@router.put("/{set_id}")
def update_set(set_id: int, concept_set: SetUpdate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concept_sets WHERE id = ?", (set_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept set not found")

    updates: list[str] = []
    params: list = []
    if concept_set.name is not None:
        updates.append("name = ?")
        params.append(concept_set.name)
    if concept_set.description is not None:
        updates.append("description = ?")
        params.append(concept_set.description)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(set_id)
    execute(f"UPDATE concept_sets SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_set(set_id, user)


@router.delete("/{set_id}", status_code=204)
def delete_set(set_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM concept_sets WHERE id = ?", (set_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept set not found")
    execute("DELETE FROM concept_set_members WHERE set_id = ?", (set_id,))
    execute("DELETE FROM concept_sets WHERE id = ?", (set_id,))


@router.get("/{set_id}/members")
def list_members(set_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    existing = query("SELECT id FROM concept_sets WHERE id = ?", (set_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept set not found")
    return query(
        """SELECT csm.*, c.name as concept_name, c.datatype, c.concept_class
           FROM concept_set_members csm
           JOIN concepts c ON csm.concept_id = c.id
           WHERE csm.set_id = ?
           ORDER BY csm.sort_order""",
        (set_id,),
    )


@router.post("/{set_id}/members", status_code=201)
def add_member(set_id: int, member: MemberCreate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concept_sets WHERE id = ?", (set_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept set not found")
    concept_exists = query("SELECT id FROM concepts WHERE id = ?", (member.concept_id,))
    if not concept_exists:
        raise HTTPException(status_code=404, detail="Concept not found")
    row_id = execute(
        "INSERT INTO concept_set_members (set_id, concept_id, sort_order) VALUES (?, ?, ?)",
        (set_id, member.concept_id, member.sort_order),
    )
    results = query(
        """SELECT csm.*, c.name as concept_name, c.datatype, c.concept_class
           FROM concept_set_members csm
           JOIN concepts c ON csm.concept_id = c.id
           WHERE csm.id = ?""",
        (row_id,),
    )
    return results[0]


@router.delete("/{set_id}/members/{member_id}", status_code=204)
def remove_member(set_id: int, member_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query(
        "SELECT id FROM concept_set_members WHERE id = ? AND set_id = ?",
        (member_id, set_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Member not found")
    execute("DELETE FROM concept_set_members WHERE id = ?", (member_id,))
