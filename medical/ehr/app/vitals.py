"""Vital signs tracking endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/patients/{patient_id}/vitals", tags=["vitals"])


class VitalCreate(BaseModel):
    visit_id: Optional[int] = None
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    respiration_rate: Optional[int] = None
    spo2: Optional[float] = None
    weight: Optional[float] = None


def _check_patient(patient_id: int) -> None:
    if not query("SELECT id FROM patients WHERE id = ?", (patient_id,)):
        raise HTTPException(status_code=404, detail="Patient not found")


@router.get("")
def list_vitals(
    patient_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    user: str = Depends(require_medical_role),
) -> list[dict]:
    _check_patient(patient_id)
    log_action(user, "list", "vitals", f"patient:{patient_id}")
    return query(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT ?",
        (patient_id, limit),
    )


@router.post("", status_code=201)
def create_vital(
    patient_id: int, vital: VitalCreate, user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    row_id = execute(
        """INSERT INTO vitals (patient_id, visit_id, temperature, pulse,
           bp_systolic, bp_diastolic, respiration_rate, spo2, weight)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            patient_id, vital.visit_id, vital.temperature, vital.pulse,
            vital.bp_systolic, vital.bp_diastolic, vital.respiration_rate,
            vital.spo2, vital.weight,
        ),
    )
    log_action(user, "create", "vitals", str(row_id))
    results = query("SELECT * FROM vitals WHERE id = ?", (row_id,))
    return results[0]


@router.get("/trends/{sign}")
def get_vital_trend(
    patient_id: int,
    sign: str,
    limit: int = Query(default=100, ge=1, le=1000),
    user: str = Depends(require_medical_role),
) -> list[dict]:
    """Return time series for a specific vital sign."""
    _check_patient(patient_id)
    valid_signs = {
        "temperature", "pulse", "bp_systolic", "bp_diastolic",
        "respiration_rate", "spo2", "weight",
    }
    if sign not in valid_signs:
        raise HTTPException(status_code=400, detail=f"Invalid vital sign. Must be one of: {', '.join(sorted(valid_signs))}")
    log_action(user, "read", "vitals_trend", f"patient:{patient_id}:{sign}")
    return query(
        f"SELECT recorded_at, {sign} FROM vitals WHERE patient_id = ? AND {sign} IS NOT NULL ORDER BY recorded_at ASC LIMIT ?",
        (patient_id, limit),
    )


# Alert thresholds
DEFAULT_THRESHOLDS = {
    "temperature": {"min": 35.0, "max": 38.5},
    "pulse": {"min": 50, "max": 100},
    "bp_systolic": {"min": 90, "max": 140},
    "bp_diastolic": {"min": 60, "max": 90},
    "respiration_rate": {"min": 12, "max": 20},
    "spo2": {"min": 92, "max": 100},
}


@router.get("/alerts")
def check_vital_alerts(
    patient_id: int, user: str = Depends(require_medical_role),
) -> list[dict]:
    """Check latest vitals against thresholds and return alerts."""
    _check_patient(patient_id)
    latest = query(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (patient_id,),
    )
    if not latest:
        return []
    record = latest[0]
    alerts: list[dict] = []
    for sign, bounds in DEFAULT_THRESHOLDS.items():
        value = record.get(sign)
        if value is None:
            continue
        if value < bounds["min"]:
            alerts.append({"sign": sign, "value": value, "level": "low", "threshold": bounds["min"]})
        elif value > bounds["max"]:
            alerts.append({"sign": sign, "value": value, "level": "high", "threshold": bounds["max"]})
    return alerts
