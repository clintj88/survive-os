"""Childbirth & Prenatal care API routes."""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/prenatal", tags=["prenatal"])

STANDARD_VISIT_WEEKS = [8, 12, 16, 20, 24, 28, 30, 32, 34, 36, 37, 38, 39, 40]
POSTPARTUM_FOLLOWUPS = ["1 day", "3 days", "1 week", "6 weeks"]
RISK_FACTORS = [
    "age_under_18", "age_over_35", "pre_eclampsia_history",
    "gestational_diabetes", "multiple_gestation", "hypertension",
    "previous_cesarean", "anemia", "obesity", "substance_use",
]


class PrenatalPatientCreate(BaseModel):
    patient_id: str
    estimated_due_date: str
    gravida: int = 1
    para: int = 0
    risk_factors: list[str] = []
    blood_type: str = ""
    rh_factor: str = ""


class PrenatalPatientUpdate(BaseModel):
    estimated_due_date: Optional[str] = None
    gravida: Optional[int] = None
    para: Optional[int] = None
    risk_factors: Optional[list[str]] = None
    blood_type: Optional[str] = None
    rh_factor: Optional[str] = None


class VisitCreate(BaseModel):
    visit_date: str
    week_number: int
    fundal_height: Optional[float] = None
    fetal_heart_rate: Optional[float] = None
    maternal_weight: Optional[float] = None
    blood_pressure: Optional[str] = None
    notes: str = ""
    provider: str = ""


class DeliveryCreate(BaseModel):
    delivery_date: str
    delivery_type: str
    complications: str = ""
    birth_weight: Optional[float] = None
    apgar_1min: Optional[int] = None
    apgar_5min: Optional[int] = None
    provider: str = ""
    notes: str = ""


class PostpartumCreate(BaseModel):
    scheduled_date: str
    followup_type: str
    completed_date: Optional[str] = None
    notes: str = ""
    provider: str = ""


@router.get("/patients")
def list_patients(_role: str = Depends(require_medical_role)) -> list[dict]:
    return query("SELECT * FROM prenatal_patients ORDER BY estimated_due_date")


@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, _role: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Patient not found")
    return rows[0]


@router.post("/patients", status_code=201)
def create_patient(data: PrenatalPatientCreate, _role: str = Depends(require_medical_role)) -> dict:
    risk_json = json.dumps(data.risk_factors)
    pid = execute(
        """INSERT INTO prenatal_patients (patient_id, estimated_due_date, gravida, para,
           risk_factors, blood_type, rh_factor) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data.patient_id, data.estimated_due_date, data.gravida, data.para,
         risk_json, data.blood_type, data.rh_factor),
    )
    return get_patient(pid)


@router.put("/patients/{patient_id}")
def update_patient(patient_id: int, data: PrenatalPatientUpdate,
                   _role: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    updates: list[str] = []
    params: list = []
    if data.estimated_due_date is not None:
        updates.append("estimated_due_date = ?")
        params.append(data.estimated_due_date)
    if data.gravida is not None:
        updates.append("gravida = ?")
        params.append(data.gravida)
    if data.para is not None:
        updates.append("para = ?")
        params.append(data.para)
    if data.risk_factors is not None:
        updates.append("risk_factors = ?")
        params.append(json.dumps(data.risk_factors))
    if data.blood_type is not None:
        updates.append("blood_type = ?")
        params.append(data.blood_type)
    if data.rh_factor is not None:
        updates.append("rh_factor = ?")
        params.append(data.rh_factor)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(patient_id)
    execute(f"UPDATE prenatal_patients SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_patient(patient_id)


@router.get("/patients/{patient_id}/schedule")
def get_visit_schedule(patient_id: int, _role: str = Depends(require_medical_role)) -> dict:
    """Generate standard prenatal visit schedule based on due date."""
    rows = query("SELECT * FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Patient not found")

    edd = datetime.fromisoformat(rows[0]["estimated_due_date"])
    conception = edd - timedelta(weeks=40)

    completed = query(
        "SELECT week_number FROM prenatal_visits WHERE prenatal_patient_id = ?",
        (patient_id,),
    )
    completed_weeks = {r["week_number"] for r in completed}

    schedule = []
    for week in STANDARD_VISIT_WEEKS:
        visit_date = (conception + timedelta(weeks=week)).isoformat()[:10]
        schedule.append({
            "week": week,
            "date": visit_date,
            "completed": week in completed_weeks,
        })
    return {"patient_id": patient_id, "schedule": schedule}


@router.get("/patients/{patient_id}/visits")
def list_visits(patient_id: int, _role: str = Depends(require_medical_role)) -> list[dict]:
    return query(
        "SELECT * FROM prenatal_visits WHERE prenatal_patient_id = ? ORDER BY week_number",
        (patient_id,),
    )


@router.post("/patients/{patient_id}/visits", status_code=201)
def create_visit(patient_id: int, data: VisitCreate,
                 _role: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    vid = execute(
        """INSERT INTO prenatal_visits (prenatal_patient_id, visit_date, week_number,
           fundal_height, fetal_heart_rate, maternal_weight, blood_pressure, notes, provider)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, data.visit_date, data.week_number, data.fundal_height,
         data.fetal_heart_rate, data.maternal_weight, data.blood_pressure,
         data.notes, data.provider),
    )
    rows = query("SELECT * FROM prenatal_visits WHERE id = ?", (vid,))
    return rows[0]


@router.get("/patients/{patient_id}/deliveries")
def list_deliveries(patient_id: int, _role: str = Depends(require_medical_role)) -> list[dict]:
    return query(
        "SELECT * FROM deliveries WHERE prenatal_patient_id = ? ORDER BY delivery_date",
        (patient_id,),
    )


@router.post("/patients/{patient_id}/deliveries", status_code=201)
def create_delivery(patient_id: int, data: DeliveryCreate,
                    _role: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    did = execute(
        """INSERT INTO deliveries (prenatal_patient_id, delivery_date, delivery_type,
           complications, birth_weight, apgar_1min, apgar_5min, provider, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, data.delivery_date, data.delivery_type, data.complications,
         data.birth_weight, data.apgar_1min, data.apgar_5min, data.provider, data.notes),
    )
    rows = query("SELECT * FROM deliveries WHERE id = ?", (did,))
    return rows[0]


@router.get("/patients/{patient_id}/postpartum")
def list_postpartum(patient_id: int, _role: str = Depends(require_medical_role)) -> list[dict]:
    return query(
        "SELECT * FROM postpartum_followups WHERE prenatal_patient_id = ? ORDER BY scheduled_date",
        (patient_id,),
    )


@router.post("/patients/{patient_id}/postpartum", status_code=201)
def create_postpartum(patient_id: int, data: PostpartumCreate,
                      _role: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM prenatal_patients WHERE id = ?", (patient_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    fid = execute(
        """INSERT INTO postpartum_followups (prenatal_patient_id, scheduled_date,
           completed_date, followup_type, notes, provider) VALUES (?, ?, ?, ?, ?, ?)""",
        (patient_id, data.scheduled_date, data.completed_date,
         data.followup_type, data.notes, data.provider),
    )
    rows = query("SELECT * FROM postpartum_followups WHERE id = ?", (fid,))
    return rows[0]


@router.get("/risk-factors")
def list_risk_factors(_role: str = Depends(require_medical_role)) -> list[str]:
    return RISK_FACTORS


@router.get("/visit-weeks")
def list_visit_weeks(_role: str = Depends(require_medical_role)) -> list[int]:
    return STANDARD_VISIT_WEEKS
