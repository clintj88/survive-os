"""Concept mapping CRUD endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/concepts", tags=["mappings"])

VALID_SOURCES = ("icd10", "snomed", "loinc", "local")


class MappingCreate(BaseModel):
    source: str
    code: str
    name: str = ""


class MappingUpdate(BaseModel):
    source: Optional[str] = None
    code: Optional[str] = None
    name: Optional[str] = None


@router.get("/{concept_id}/mappings")
def list_mappings(concept_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")
    return query(
        "SELECT * FROM concept_mappings WHERE concept_id = ? ORDER BY source, code",
        (concept_id,),
    )


@router.post("/{concept_id}/mappings", status_code=201)
def create_mapping(concept_id: int, mapping: MappingCreate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM concepts WHERE id = ?", (concept_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Concept not found")
    if mapping.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(VALID_SOURCES)}",
        )
    row_id = execute(
        "INSERT INTO concept_mappings (concept_id, source, code, name) VALUES (?, ?, ?, ?)",
        (concept_id, mapping.source, mapping.code, mapping.name),
    )
    results = query("SELECT * FROM concept_mappings WHERE id = ?", (row_id,))
    return results[0]


@router.put("/{concept_id}/mappings/{mapping_id}")
def update_mapping(
    concept_id: int,
    mapping_id: int,
    mapping: MappingUpdate,
    user: str = Depends(require_medical_role),
) -> dict:
    existing = query(
        "SELECT * FROM concept_mappings WHERE id = ? AND concept_id = ?",
        (mapping_id, concept_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Mapping not found")

    updates: list[str] = []
    params: list = []
    if mapping.source is not None:
        if mapping.source not in VALID_SOURCES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source. Must be one of: {', '.join(VALID_SOURCES)}",
            )
        updates.append("source = ?")
        params.append(mapping.source)
    if mapping.code is not None:
        updates.append("code = ?")
        params.append(mapping.code)
    if mapping.name is not None:
        updates.append("name = ?")
        params.append(mapping.name)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(mapping_id)
    execute(f"UPDATE concept_mappings SET {', '.join(updates)} WHERE id = ?", tuple(params))
    results = query("SELECT * FROM concept_mappings WHERE id = ?", (mapping_id,))
    return results[0]


@router.delete("/{concept_id}/mappings/{mapping_id}", status_code=204)
def delete_mapping(concept_id: int, mapping_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query(
        "SELECT id FROM concept_mappings WHERE id = ? AND concept_id = ?",
        (mapping_id, concept_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Mapping not found")
    execute("DELETE FROM concept_mappings WHERE id = ?", (mapping_id,))
