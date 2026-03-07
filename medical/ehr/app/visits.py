"""SOAP visit notes endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .audit import log_action
from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/patients/{patient_id}/visits", tags=["visits"])


class VisitCreate(BaseModel):
    provider: str
    visit_date: Optional[str] = None
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    notes: str = ""


class VisitUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None


def _check_patient(patient_id: int) -> None:
    if not query("SELECT id FROM patients WHERE id = ?", (patient_id,)):
        raise HTTPException(status_code=404, detail="Patient not found")


@router.get("")
def list_visits(patient_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    _check_patient(patient_id)
    log_action(user, "list", "visit", f"patient:{patient_id}")
    return query(
        "SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC",
        (patient_id,),
    )


@router.get("/{visit_id}")
def get_visit(patient_id: int, visit_id: int, user: str = Depends(require_medical_role)) -> dict:
    _check_patient(patient_id)
    results = query(
        "SELECT * FROM visits WHERE id = ? AND patient_id = ?",
        (visit_id, patient_id),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Visit not found")
    log_action(user, "read", "visit", str(visit_id))
    return results[0]


@router.post("", status_code=201)
def create_visit(patient_id: int, visit: VisitCreate, user: str = Depends(require_medical_role)) -> dict:
    _check_patient(patient_id)
    params = (
        patient_id, visit.provider, visit.subjective,
        visit.objective, visit.assessment, visit.plan, visit.notes,
    )
    if visit.visit_date:
        row_id = execute(
            """INSERT INTO visits (patient_id, provider, subjective, objective, assessment, plan, notes, visit_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            params + (visit.visit_date,),
        )
    else:
        row_id = execute(
            """INSERT INTO visits (patient_id, provider, subjective, objective, assessment, plan, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            params,
        )
    log_action(user, "create", "visit", str(row_id))
    return get_visit(patient_id, row_id, user)


@router.put("/{visit_id}")
def update_visit(
    patient_id: int, visit_id: int, visit: VisitUpdate,
    user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    existing = query("SELECT id FROM visits WHERE id = ? AND patient_id = ?", (visit_id, patient_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Visit not found")

    updates: list[str] = []
    params: list = []
    for field in ["subjective", "objective", "assessment", "plan", "notes"]:
        val = getattr(visit, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(visit_id)
    execute(f"UPDATE visits SET {', '.join(updates)} WHERE id = ?", tuple(params))
    log_action(user, "update", "visit", str(visit_id))
    return get_visit(patient_id, visit_id, user)
