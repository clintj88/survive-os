"""Wound care log endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .audit import log_action
from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/patients/{patient_id}/wounds", tags=["wounds"])


class WoundCreate(BaseModel):
    body_location: str
    wound_type: str
    size: str = ""


class WoundEntryCreate(BaseModel):
    treatment_notes: str = ""
    photo_path: str = ""
    healing_status: str = "ongoing"


class WoundStatusUpdate(BaseModel):
    status: Optional[str] = None
    size: Optional[str] = None


def _check_patient(patient_id: int) -> None:
    if not query("SELECT id FROM patients WHERE id = ?", (patient_id,)):
        raise HTTPException(status_code=404, detail="Patient not found")


@router.get("")
def list_wounds(patient_id: int, user: str = Depends(require_medical_role)) -> list[dict]:
    _check_patient(patient_id)
    log_action(user, "list", "wound", f"patient:{patient_id}")
    return query(
        "SELECT * FROM wounds WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,),
    )


@router.post("", status_code=201)
def create_wound(
    patient_id: int, wound: WoundCreate, user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    row_id = execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type, size) VALUES (?, ?, ?, ?)",
        (patient_id, wound.body_location, wound.wound_type, wound.size),
    )
    log_action(user, "create", "wound", str(row_id))
    return query("SELECT * FROM wounds WHERE id = ?", (row_id,))[0]


@router.get("/{wound_id}")
def get_wound(
    patient_id: int, wound_id: int, user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    results = query(
        "SELECT * FROM wounds WHERE id = ? AND patient_id = ?",
        (wound_id, patient_id),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Wound not found")
    wound = results[0]
    wound["entries"] = query(
        "SELECT * FROM wound_entries WHERE wound_id = ? ORDER BY entry_date DESC",
        (wound_id,),
    )
    log_action(user, "read", "wound", str(wound_id))
    return wound


@router.put("/{wound_id}")
def update_wound(
    patient_id: int, wound_id: int, update: WoundStatusUpdate,
    user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    existing = query("SELECT id FROM wounds WHERE id = ? AND patient_id = ?", (wound_id, patient_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Wound not found")
    updates: list[str] = []
    params: list = []
    if update.status is not None:
        updates.append("status = ?")
        params.append(update.status)
    if update.size is not None:
        updates.append("size = ?")
        params.append(update.size)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(wound_id)
    execute(f"UPDATE wounds SET {', '.join(updates)} WHERE id = ?", tuple(params))
    log_action(user, "update", "wound", str(wound_id))
    return query("SELECT * FROM wounds WHERE id = ?", (wound_id,))[0]


@router.post("/{wound_id}/entries", status_code=201)
def add_wound_entry(
    patient_id: int, wound_id: int, entry: WoundEntryCreate,
    user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    wound = query("SELECT id FROM wounds WHERE id = ? AND patient_id = ?", (wound_id, patient_id))
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    row_id = execute(
        "INSERT INTO wound_entries (wound_id, treatment_notes, photo_path, healing_status) VALUES (?, ?, ?, ?)",
        (wound_id, entry.treatment_notes, entry.photo_path, entry.healing_status),
    )
    log_action(user, "create", "wound_entry", str(row_id))
    return query("SELECT * FROM wound_entries WHERE id = ?", (row_id,))[0]


@router.get("/{wound_id}/entries")
def list_wound_entries(
    patient_id: int, wound_id: int, user: str = Depends(require_medical_role),
) -> list[dict]:
    _check_patient(patient_id)
    wound = query("SELECT id FROM wounds WHERE id = ? AND patient_id = ?", (wound_id, patient_id))
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    log_action(user, "list", "wound_entry", f"wound:{wound_id}")
    return query(
        "SELECT * FROM wound_entries WHERE wound_id = ? ORDER BY entry_date DESC",
        (wound_id,),
    )
