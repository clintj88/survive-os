"""Test catalog router — CRUD for lab test definitions."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


class TestCreate(BaseModel):
    name: str
    concept_id: str | None = None
    specimen_type: str = "blood"
    ref_range_min: float | None = None
    ref_range_max: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    units: str = ""
    description: str = ""
    turnaround_hours: int = 24
    active: int = 1


class TestUpdate(BaseModel):
    name: str | None = None
    concept_id: str | None = None
    specimen_type: str | None = None
    ref_range_min: float | None = None
    ref_range_max: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    units: str | None = None
    description: str | None = None
    turnaround_hours: int | None = None
    active: int | None = None


@router.get("")
def list_tests(
    active: int | None = None,
    specimen_type: str | None = None,
    _user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = "SELECT * FROM test_catalog WHERE 1=1"
    params: list = []
    if active is not None:
        sql += " AND active = ?"
        params.append(active)
    if specimen_type:
        sql += " AND specimen_type = ?"
        params.append(specimen_type)
    sql += " ORDER BY name"
    return query(sql, tuple(params))


@router.get("/{test_id}")
def get_test(test_id: int, _user: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM test_catalog WHERE id = ?", (test_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Test not found")
    return rows[0]


@router.post("", status_code=201)
def create_test(body: TestCreate, _user: str = Depends(require_medical_role)) -> dict:
    row_id = execute(
        """INSERT INTO test_catalog
           (name, concept_id, specimen_type, ref_range_min, ref_range_max,
            critical_low, critical_high, units, description, turnaround_hours, active)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.name, body.concept_id, body.specimen_type,
         body.ref_range_min, body.ref_range_max,
         body.critical_low, body.critical_high,
         body.units, body.description, body.turnaround_hours, body.active),
    )
    return query("SELECT * FROM test_catalog WHERE id = ?", (row_id,))[0]


@router.put("/{test_id}")
def update_test(
    test_id: int, body: TestUpdate, _user: str = Depends(require_medical_role),
) -> dict:
    existing = query("SELECT * FROM test_catalog WHERE id = ?", (test_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Test not found")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return existing[0]
    sets = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values())
    vals.append(test_id)
    execute(
        f"UPDATE test_catalog SET {sets}, updated_at = datetime('now') WHERE id = ?",
        tuple(vals),
    )
    return query("SELECT * FROM test_catalog WHERE id = ?", (test_id,))[0]


@router.delete("/{test_id}", status_code=204)
def delete_test(test_id: int, _user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT * FROM test_catalog WHERE id = ?", (test_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Test not found")
    execute("DELETE FROM test_catalog WHERE id = ?", (test_id,))
