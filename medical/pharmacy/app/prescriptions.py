"""Prescription tracking routes."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])


class PrescriptionCreate(BaseModel):
    patient_id: str
    medication_id: int
    dosage: str
    frequency: str
    duration: str = ""
    prescriber: str
    refills_remaining: int = 0
    notes: str = ""


class PrescriptionUpdate(BaseModel):
    status: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    refills_remaining: Optional[int] = None
    notes: Optional[str] = None


@router.get("")
def list_prescriptions(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if patient_id:
        conditions.append("p.patient_id = ?")
        params.append(patient_id)
    if status:
        conditions.append("p.status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT p.*, m.name as medication_name, m.generic_name, m.form, m.strength
            FROM prescriptions p
            JOIN medications m ON p.medication_id = m.id
            {where}
            ORDER BY p.date_prescribed DESC""",
        tuple(params),
    )


@router.get("/{rx_id}")
def get_prescription(
    rx_id: int,
    _role: str = Depends(require_medical_role),
) -> dict:
    results = query(
        """SELECT p.*, m.name as medication_name, m.generic_name, m.form, m.strength
           FROM prescriptions p
           JOIN medications m ON p.medication_id = m.id
           WHERE p.id = ?""",
        (rx_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Prescription not found")
    rx = results[0]
    rx["dispensing_history"] = query(
        """SELECT d.*, l.lot_number
           FROM dispensing_log d
           JOIN inventory_lots l ON d.lot_id = l.id
           WHERE d.prescription_id = ?
           ORDER BY d.date_dispensed DESC""",
        (rx_id,),
    )
    return rx


@router.post("", status_code=201)
def create_prescription(
    rx: PrescriptionCreate,
    _role: str = Depends(require_medical_role),
) -> dict:
    meds = query("SELECT id FROM medications WHERE id = ?", (rx.medication_id,))
    if not meds:
        raise HTTPException(status_code=400, detail="Medication not found")
    rx_id = execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, duration, prescriber, refills_remaining, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (rx.patient_id, rx.medication_id, rx.dosage, rx.frequency,
         rx.duration, rx.prescriber, rx.refills_remaining, rx.notes),
    )
    return get_prescription(rx_id)


@router.put("/{rx_id}")
def update_prescription(
    rx_id: int,
    rx: PrescriptionUpdate,
    _role: str = Depends(require_medical_role),
) -> dict:
    existing = query("SELECT id FROM prescriptions WHERE id = ?", (rx_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Prescription not found")
    updates: list[str] = []
    params: list = []
    for field in ["status", "dosage", "frequency", "refills_remaining", "notes"]:
        value = getattr(rx, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(rx_id)
    execute(f"UPDATE prescriptions SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_prescription(rx_id)


@router.get("/patient/{patient_id}/active")
def get_active_prescriptions(
    patient_id: str,
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    return query(
        """SELECT p.*, m.name as medication_name, m.generic_name, m.form, m.strength
           FROM prescriptions p
           JOIN medications m ON p.medication_id = m.id
           WHERE p.patient_id = ? AND p.status = 'active'
           ORDER BY p.date_prescribed DESC""",
        (patient_id,),
    )
