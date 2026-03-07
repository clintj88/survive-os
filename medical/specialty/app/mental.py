"""Mental Health API routes - PRIVACY-FIRST DESIGN.

All data is voluntary. No mandatory reporting. No diagnosis codes.
No involuntary holds. No data sharing without explicit consent.
Patient controls their own data.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import require_medical_role
from .database import execute, query
from seed.mental_resources import COPING_STRATEGIES, SELF_CARE_TIPS, CRISIS_INFO

router = APIRouter(prefix="/api/mental", tags=["mental_health"])


class CheckinCreate(BaseModel):
    patient_id: str
    mood: int = Field(ge=1, le=5)
    sleep_quality: int = Field(ge=1, le=5)
    appetite: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    anxiety_level: int = Field(ge=1, le=5)
    notes: str = ""


class ProviderNoteCreate(BaseModel):
    patient_id: str
    provider: str
    note: str
    patient_consent: bool


@router.get("/checkins/{patient_id}")
def list_checkins(patient_id: str, limit: int = 30,
                  _role: str = Depends(require_medical_role)) -> list[dict]:
    return query(
        "SELECT * FROM mental_checkins WHERE patient_id = ? ORDER BY checkin_date DESC LIMIT ?",
        (patient_id, limit),
    )


@router.post("/checkins", status_code=201)
def create_checkin(data: CheckinCreate, _role: str = Depends(require_medical_role)) -> dict:
    cid = execute(
        """INSERT INTO mental_checkins (patient_id, mood, sleep_quality, appetite,
           energy, anxiety_level, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data.patient_id, data.mood, data.sleep_quality, data.appetite,
         data.energy, data.anxiety_level, data.notes),
    )
    rows = query("SELECT * FROM mental_checkins WHERE id = ?", (cid,))
    return rows[0]


@router.get("/checkins/{patient_id}/trends")
def get_trends(patient_id: str, days: int = 30,
               _role: str = Depends(require_medical_role)) -> dict:
    """Get trend data for wellness scores over time."""
    rows = query(
        """SELECT checkin_date, mood, sleep_quality, appetite, energy, anxiety_level
           FROM mental_checkins WHERE patient_id = ?
           AND checkin_date >= datetime('now', ?)
           ORDER BY checkin_date""",
        (patient_id, f"-{days} days"),
    )
    if not rows:
        return {"patient_id": patient_id, "days": days, "data": [], "averages": {}}

    averages = {
        "mood": sum(r["mood"] for r in rows) / len(rows),
        "sleep_quality": sum(r["sleep_quality"] for r in rows) / len(rows),
        "appetite": sum(r["appetite"] for r in rows) / len(rows),
        "energy": sum(r["energy"] for r in rows) / len(rows),
        "anxiety_level": sum(r["anxiety_level"] for r in rows) / len(rows),
    }
    return {"patient_id": patient_id, "days": days, "data": rows, "averages": averages}


@router.delete("/checkins/{checkin_id}")
def delete_checkin(checkin_id: int, patient_id: str,
                   _role: str = Depends(require_medical_role)) -> dict:
    """Patient can delete their own check-in data."""
    existing = query(
        "SELECT id FROM mental_checkins WHERE id = ? AND patient_id = ?",
        (checkin_id, patient_id),
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Check-in not found")
    execute("DELETE FROM mental_checkins WHERE id = ?", (checkin_id,))
    return {"deleted": True}


@router.get("/notes/{patient_id}")
def list_provider_notes(patient_id: str, _role: str = Depends(require_medical_role)) -> list[dict]:
    """Only returns notes where patient gave explicit consent."""
    return query(
        "SELECT * FROM mental_provider_notes WHERE patient_id = ? AND patient_consent = 1 ORDER BY created_at DESC",
        (patient_id,),
    )


@router.post("/notes", status_code=201)
def create_provider_note(data: ProviderNoteCreate,
                         _role: str = Depends(require_medical_role)) -> dict:
    if not data.patient_consent:
        raise HTTPException(
            status_code=400,
            detail="Patient consent is required to store provider notes",
        )
    nid = execute(
        "INSERT INTO mental_provider_notes (patient_id, provider, note, patient_consent) VALUES (?, ?, ?, ?)",
        (data.patient_id, data.provider, data.note, 1),
    )
    rows = query("SELECT * FROM mental_provider_notes WHERE id = ?", (nid,))
    return rows[0]


@router.get("/resources")
def get_resources(_role: str = Depends(require_medical_role)) -> dict:
    return {
        "coping_strategies": COPING_STRATEGIES,
        "self_care_tips": SELF_CARE_TIPS,
        "crisis_info": CRISIS_INFO,
    }
