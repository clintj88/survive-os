"""Dental care API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/dental", tags=["dental"])

ADULT_TEETH = list(range(1, 33))
PEDIATRIC_TEETH = list(range(1, 21))
TOOTH_STATUSES = ["healthy", "cavity", "filling", "crown", "extraction", "missing", "root_canal"]

EMERGENCY_PROTOCOLS = [
    {
        "condition": "Knocked-out tooth",
        "steps": [
            "Hold tooth by crown, never touch root",
            "Rinse gently with milk or saline if dirty",
            "Try to reinsert into socket",
            "If unable, store in milk or patient's saliva",
            "Seek dental care within 30 minutes for best outcome",
        ],
    },
    {
        "condition": "Severe toothache",
        "steps": [
            "Rinse mouth with warm salt water",
            "Use dental floss to remove trapped food",
            "Apply cold compress to outside of cheek",
            "Administer pain relief (ibuprofen preferred)",
            "Do not apply aspirin directly to gum tissue",
        ],
    },
    {
        "condition": "Dental abscess",
        "steps": [
            "Rinse with warm salt water multiple times daily",
            "Administer antibiotics if available (amoxicillin 500mg TID)",
            "Pain management with ibuprofen/acetaminophen",
            "Do not squeeze or puncture abscess",
            "Incision and drainage may be needed by provider",
        ],
    },
    {
        "condition": "Broken jaw",
        "steps": [
            "Stabilize jaw - do not attempt to realign",
            "Apply cold compress to reduce swelling",
            "Bandage to support jaw (chin to top of head)",
            "Monitor airway - keep patient upright",
            "Seek surgical care as soon as possible",
        ],
    },
]


class DentalPatientCreate(BaseModel):
    patient_id: str
    is_pediatric: bool = False


class ToothUpdate(BaseModel):
    status: str
    notes: str = ""


class TreatmentCreate(BaseModel):
    tooth_number: int
    procedure_type: str
    provider: str = ""
    notes: str = ""
    treatment_date: Optional[str] = None


class PreventiveCreate(BaseModel):
    last_cleaning: Optional[str] = None
    next_cleaning: Optional[str] = None
    notes: str = ""


@router.get("/patients")
def list_patients(_role: str = Depends(require_medical_role)) -> list[dict]:
    return query("SELECT * FROM dental_patients ORDER BY patient_id")


@router.get("/patients/{patient_id}")
def get_patient(patient_id: int, _role: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM dental_patients WHERE id = ?", (patient_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Patient not found")
    return rows[0]


@router.post("/patients", status_code=201)
def create_patient(data: DentalPatientCreate, _role: str = Depends(require_medical_role)) -> dict:
    pid = execute(
        "INSERT INTO dental_patients (patient_id, is_pediatric) VALUES (?, ?)",
        (data.patient_id, 1 if data.is_pediatric else 0),
    )
    return get_patient(pid)


@router.get("/patients/{patient_id}/chart")
def get_tooth_chart(patient_id: int, _role: str = Depends(require_medical_role)) -> dict:
    patient = query("SELECT * FROM dental_patients WHERE id = ?", (patient_id,))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    teeth_range = PEDIATRIC_TEETH if patient[0]["is_pediatric"] else ADULT_TEETH
    chart_data = query(
        "SELECT * FROM tooth_chart WHERE dental_patient_id = ?", (patient_id,)
    )
    chart_map = {r["tooth_number"]: r for r in chart_data}

    chart = []
    for tooth in teeth_range:
        if tooth in chart_map:
            chart.append(chart_map[tooth])
        else:
            chart.append({
                "tooth_number": tooth,
                "status": "healthy",
                "notes": "",
            })
    return {"patient_id": patient_id, "is_pediatric": bool(patient[0]["is_pediatric"]), "teeth": chart}


@router.put("/patients/{patient_id}/chart/{tooth_number}")
def update_tooth(patient_id: int, tooth_number: int, data: ToothUpdate,
                 _role: str = Depends(require_medical_role)) -> dict:
    patient = query("SELECT * FROM dental_patients WHERE id = ?", (patient_id,))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if data.status not in TOOTH_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {TOOTH_STATUSES}")

    max_tooth = 20 if patient[0]["is_pediatric"] else 32
    if tooth_number < 1 or tooth_number > max_tooth:
        raise HTTPException(status_code=400, detail=f"Invalid tooth number (1-{max_tooth})")

    existing = query(
        "SELECT id FROM tooth_chart WHERE dental_patient_id = ? AND tooth_number = ?",
        (patient_id, tooth_number),
    )
    if existing:
        execute(
            "UPDATE tooth_chart SET status = ?, notes = ?, updated_at = datetime('now') WHERE id = ?",
            (data.status, data.notes, existing[0]["id"]),
        )
    else:
        execute(
            "INSERT INTO tooth_chart (dental_patient_id, tooth_number, status, notes) VALUES (?, ?, ?, ?)",
            (patient_id, tooth_number, data.status, data.notes),
        )
    return {"tooth_number": tooth_number, "status": data.status, "notes": data.notes}


@router.get("/patients/{patient_id}/treatments")
def list_treatments(patient_id: int, _role: str = Depends(require_medical_role)) -> list[dict]:
    return query(
        "SELECT * FROM dental_treatments WHERE dental_patient_id = ? ORDER BY treatment_date DESC",
        (patient_id,),
    )


@router.post("/patients/{patient_id}/treatments", status_code=201)
def create_treatment(patient_id: int, data: TreatmentCreate,
                     _role: str = Depends(require_medical_role)) -> dict:
    patient = query("SELECT * FROM dental_patients WHERE id = ?", (patient_id,))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    tid = execute(
        """INSERT INTO dental_treatments (dental_patient_id, tooth_number, procedure_type,
           provider, notes, treatment_date) VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))""",
        (patient_id, data.tooth_number, data.procedure_type, data.provider,
         data.notes, data.treatment_date),
    )
    rows = query("SELECT * FROM dental_treatments WHERE id = ?", (tid,))
    return rows[0]


@router.get("/patients/{patient_id}/preventive")
def get_preventive(patient_id: int, _role: str = Depends(require_medical_role)) -> dict:
    rows = query(
        "SELECT * FROM dental_preventive WHERE dental_patient_id = ?", (patient_id,)
    )
    if not rows:
        return {"dental_patient_id": patient_id, "last_cleaning": None, "next_cleaning": None, "notes": ""}
    return rows[0]


@router.post("/patients/{patient_id}/preventive", status_code=201)
def set_preventive(patient_id: int, data: PreventiveCreate,
                   _role: str = Depends(require_medical_role)) -> dict:
    patient = query("SELECT * FROM dental_patients WHERE id = ?", (patient_id,))
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = query("SELECT id FROM dental_preventive WHERE dental_patient_id = ?", (patient_id,))
    if existing:
        execute(
            "UPDATE dental_preventive SET last_cleaning = ?, next_cleaning = ?, notes = ? WHERE id = ?",
            (data.last_cleaning, data.next_cleaning, data.notes, existing[0]["id"]),
        )
    else:
        execute(
            "INSERT INTO dental_preventive (dental_patient_id, last_cleaning, next_cleaning, notes) VALUES (?, ?, ?, ?)",
            (patient_id, data.last_cleaning, data.next_cleaning, data.notes),
        )
    return get_preventive(patient_id)


@router.get("/emergency-protocols")
def get_emergency_protocols(_role: str = Depends(require_medical_role)) -> list[dict]:
    return EMERGENCY_PROTOCOLS


@router.get("/statuses")
def get_statuses(_role: str = Depends(require_medical_role)) -> list[str]:
    return TOOTH_STATUSES
