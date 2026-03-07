"""Concept CRUD endpoints."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/concepts", tags=["concepts"])

VALID_DATATYPES = ("numeric", "coded", "text", "boolean", "date", "datetime")
VALID_CLASSES = ("diagnosis", "symptom", "test", "drug", "procedure", "finding", "misc")


class ConceptCreate(BaseModel):
    name: str
    short_name: str = ""
    datatype: str
    concept_class: str
    description: str = ""
    units: str = ""


class ConceptUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    datatype: Optional[str] = None
    concept_class: Optional[str] = None
    description: Optional[str] = None
    units: Optional[str] = None


class AnswerCreate(BaseModel):
    answer_concept_id: int
    sort_order: int = 0


def _validate_datatype(datatype: str) -> None:
    if datatype not in VALID_DATATYPES:
        raise HTTPException(status_code=400, detail=f"Invalid datatype. Must be one of: {', '.join(VALID_DATATYPES)}")


def _validate_class(concept_class: str) -> None:
    if concept_class not in VALID_CLASSES:
        raise HTTPException(status_code=400, detail=f"Invalid concept_class. Must be one of: {', '.join(VALID_CLASSES)}")


@router.get("/search")
def search_concepts(
    q: Optional[str] = Query(None),
    concept_class: Optional[str] = Query(None, alias="class"),
    source: Optional[str] = Query(None),
    user: str = Depends(require_medical_role),
) -> list[dict]:
    if source:
        sql = """SELECT DISTINCT c.* FROM concepts c
                 JOIN concept_mappings m ON c.id = m.concept_id
                 WHERE c.retired = 0"""
        conditions: list[str] = []
        params: list = []
        conditions.append("m.source = ?")
        params.append(source)
        if q:
            conditions.append("c.name LIKE ?")
            params.append(f"%{q}%")
        if concept_class:
            conditions.append("c.concept_class = ?")
            params.append(concept_class)
        if conditions:
            sql += " AND " + " AND ".join(conditions)
        sql += " ORDER BY c.name"
        return query(sql, tuple(params))

    sql = "SELECT * FROM concepts WHERE retired = 0"
    conditions = []
    params = []
    if q:
        conditions.append("name LIKE ?")
        params.append(f"%{q}%")
    if concept_class:
        conditions.append("concept_class = ?")
        params.append(concept_class)
    if conditions:
        sql += " AND " + " AND ".join(conditions)
    sql += " ORDER BY name"
    return query(sql, tuple(params))


@router.get("")
def list_concepts(
    include_retired: bool = Query(False),
    user: str = Depends(require_medical_role),
) -> list[dict]:
    if include_retired:
        return query("SELECT * FROM concepts ORDER BY name")
    return query("SELECT * FROM concepts WHERE retired = 0 ORDER BY name")


@router.get("/{concept_id}")
def get_concept(concept_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Concept not found")
    concept = results[0]
    concept["answers"] = query(
        "SELECT * FROM concept_answers WHERE concept_id = ? ORDER BY sort_order",
        (concept_id,),
    )
    concept["mappings"] = query(
        "SELECT * FROM concept_mappings WHERE concept_id = ?",
        (concept_id,),
    )
    return concept


@router.post("", status_code=201)
def create_concept(concept: ConceptCreate, user: str = Depends(require_medical_role)) -> dict:
    _validate_datatype(concept.datatype)
    _validate_class(concept.concept_class)
    row_id = execute(
        """INSERT INTO concepts (name, short_name, datatype, concept_class, description, units)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (concept.name, concept.short_name, concept.datatype,
         concept.concept_class, concept.description, concept.units),
    )
    return get_concept(row_id, user)


@router.put("/{concept_id}")
def update_concept(concept_id: int, concept: ConceptUpdate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")

    updates: list[str] = []
    params: list = []
    if concept.name is not None:
        updates.append("name = ?")
        params.append(concept.name)
    if concept.short_name is not None:
        updates.append("short_name = ?")
        params.append(concept.short_name)
    if concept.datatype is not None:
        _validate_datatype(concept.datatype)
        updates.append("datatype = ?")
        params.append(concept.datatype)
    if concept.concept_class is not None:
        _validate_class(concept.concept_class)
        updates.append("concept_class = ?")
        params.append(concept.concept_class)
    if concept.description is not None:
        updates.append("description = ?")
        params.append(concept.description)
    if concept.units is not None:
        updates.append("units = ?")
        params.append(concept.units)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(concept_id)
    execute(f"UPDATE concepts SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_concept(concept_id, user)


@router.post("/{concept_id}/retire")
def retire_concept(concept_id: int, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")
    execute(
        "UPDATE concepts SET retired = 1, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), concept_id),
    )
    return get_concept(concept_id, user)


@router.post("/{concept_id}/unretire")
def unretire_concept(concept_id: int, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")
    execute(
        "UPDATE concepts SET retired = 0, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), concept_id),
    )
    return get_concept(concept_id, user)


@router.post("/{concept_id}/answers", status_code=201)
def add_answer(concept_id: int, answer: AnswerCreate, user: str = Depends(require_medical_role)) -> dict:
    concept = query("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    if concept[0]["datatype"] != "coded":
        raise HTTPException(status_code=400, detail="Only coded concepts can have answers")
    answer_exists = query("SELECT id FROM concepts WHERE id = ?", (answer.answer_concept_id,))
    if not answer_exists:
        raise HTTPException(status_code=404, detail="Answer concept not found")
    row_id = execute(
        "INSERT INTO concept_answers (concept_id, answer_concept_id, sort_order) VALUES (?, ?, ?)",
        (concept_id, answer.answer_concept_id, answer.sort_order),
    )
    results = query("SELECT * FROM concept_answers WHERE id = ?", (row_id,))
    return results[0]


@router.get("/{concept_id}/answers")
def list_answers(concept_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")
    return query(
        "SELECT * FROM concept_answers WHERE concept_id = ? ORDER BY sort_order",
        (concept_id,),
    )


@router.delete("/{concept_id}/answers/{answer_id}", status_code=204)
def delete_answer(concept_id: int, answer_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query(
        "SELECT id FROM concept_answers WHERE id = ? AND concept_id = ?",
        (answer_id, concept_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Answer not found")
    execute("DELETE FROM concept_answers WHERE id = ?", (answer_id,))
