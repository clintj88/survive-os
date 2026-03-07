"""Patient records CRUD endpoints."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    sex: str
    blood_type: str = ""
    allergies: list[str] = []
    chronic_conditions: list[str] = []
    emergency_contact: str = ""
    photo_path: str = ""
    notes: str = ""


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None
    emergency_contact: Optional[str] = None
    photo_path: Optional[str] = None
    notes: Optional[str] = None


def _format_patient(row: dict) -> dict:
    """Parse JSON fields in patient row."""
    row["allergies"] = json.loads(row.get("allergies", "[]"))
    row["chronic_conditions"] = json.loads(row.get("chronic_conditions", "[]"))
    return row


@router.get("")
def list_patients(
    name: Optional[str] = Query(None),
    dob: Optional[str] = Query(None),
    blood_type: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = "SELECT * FROM patients"
    conditions: list[str] = []
    params: list = []
    if name:
        conditions.append("(first_name LIKE ? OR last_name LIKE ?)")
        params.extend([f"%{name}%", f"%{name}%"])
    if dob:
        conditions.append("date_of_birth = ?")
        params.append(dob)
    if blood_type:
        conditions.append("blood_type = ?")
        params.append(blood_type)
    if condition:
        conditions.append("chronic_conditions LIKE ?")
        params.append(f"%{condition}%")
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY last_name, first_name"
    log_action(user, "list", "patient")
    return [_format_patient(r) for r in query(sql, tuple(params))]


@router.get("/{patient_id}")
def get_patient(patient_id: int, user: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Patient not found")
    log_action(user, "read", "patient", str(patient_id))
    return _format_patient(results[0])


@router.post("", status_code=201)
def create_patient(patient: PatientCreate, user: str = Depends(require_medical_role)) -> dict:
    pid = f"P-{uuid.uuid4().hex[:8].upper()}"
    row_id = execute(
        """INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, sex,
           blood_type, allergies, chronic_conditions, emergency_contact, photo_path, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            pid, patient.first_name, patient.last_name, patient.date_of_birth,
            patient.sex, patient.blood_type, json.dumps(patient.allergies),
            json.dumps(patient.chronic_conditions), patient.emergency_contact,
            patient.photo_path, patient.notes,
        ),
    )
    log_action(user, "create", "patient", str(row_id))
    return get_patient(row_id, user)


@router.put("/{patient_id}")
def update_patient(patient_id: int, patient: PatientUpdate, user: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    updates: list[str] = []
    params: list = []
    for field in ["first_name", "last_name", "date_of_birth", "sex", "blood_type",
                  "emergency_contact", "photo_path", "notes"]:
        val = getattr(patient, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if patient.allergies is not None:
        updates.append("allergies = ?")
        params.append(json.dumps(patient.allergies))
    if patient.chronic_conditions is not None:
        updates.append("chronic_conditions = ?")
        params.append(json.dumps(patient.chronic_conditions))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(patient_id)
    execute(f"UPDATE patients SET {', '.join(updates)} WHERE id = ?", tuple(params))
    log_action(user, "update", "patient", str(patient_id))
    return get_patient(patient_id, user)


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int, user: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")
    execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    log_action(user, "delete", "patient", str(patient_id))
