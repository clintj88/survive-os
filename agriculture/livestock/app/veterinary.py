"""Veterinary treatment log and medication tracking."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/vet", tags=["veterinary"])


class TreatmentCreate(BaseModel):
    animal_id: int
    date: Optional[str] = None
    condition: str
    treatment: str
    medication: str = ""
    dosage: str = ""
    administered_by: str = ""
    withdrawal_days: int = 0
    notes: str = ""


class MedicationCreate(BaseModel):
    name: str
    type: str = ""
    quantity: float = 0
    unit: str = "doses"
    low_threshold: float = 5
    default_withdrawal_days: int = 0
    notes: str = ""


class MedicationUpdate(BaseModel):
    quantity: Optional[float] = None
    low_threshold: Optional[float] = None
    notes: Optional[str] = None


class VaccinationCreate(BaseModel):
    animal_id: int
    vaccine: str
    date_given: str
    next_due_date: Optional[str] = None
    administered_by: str = ""
    notes: str = ""


# --- Treatments ---

@router.get("/treatments")
def list_treatments(animal_id: Optional[int] = Query(None)) -> list[dict]:
    if animal_id:
        return query(
            """SELECT t.*, a.name as animal_name
               FROM treatments t JOIN animals a ON t.animal_id = a.id
               WHERE t.animal_id = ? ORDER BY t.date DESC""",
            (animal_id,),
        )
    return query(
        """SELECT t.*, a.name as animal_name
           FROM treatments t JOIN animals a ON t.animal_id = a.id
           ORDER BY t.date DESC"""
    )


@router.post("/treatments", status_code=201)
def create_treatment(treatment: TreatmentCreate) -> dict:
    animal = query("SELECT id FROM animals WHERE id = ?", (treatment.animal_id,))
    if not animal:
        raise HTTPException(status_code=400, detail="Animal not found")

    date = treatment.date or datetime.now().strftime("%Y-%m-%d")
    withdrawal_end = None
    if treatment.withdrawal_days > 0:
        end = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=treatment.withdrawal_days)
        withdrawal_end = end.strftime("%Y-%m-%d")

    tid = execute(
        """INSERT INTO treatments (animal_id, date, condition, treatment, medication,
           dosage, administered_by, withdrawal_days, withdrawal_end_date, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            treatment.animal_id, date, treatment.condition, treatment.treatment,
            treatment.medication, treatment.dosage, treatment.administered_by,
            treatment.withdrawal_days, withdrawal_end, treatment.notes,
        ),
    )

    # Deduct medication from inventory if tracked
    if treatment.medication:
        meds = query(
            "SELECT * FROM medications WHERE name = ?", (treatment.medication,)
        )
        if meds and meds[0]["quantity"] > 0:
            execute(
                "UPDATE medications SET quantity = quantity - 1, updated_at = datetime('now') WHERE id = ?",
                (meds[0]["id"],),
            )

    return query(
        """SELECT t.*, a.name as animal_name
           FROM treatments t JOIN animals a ON t.animal_id = a.id
           WHERE t.id = ?""",
        (tid,),
    )[0]


@router.get("/withdrawals")
def active_withdrawals() -> list[dict]:
    """Return animals with active withdrawal periods."""
    return query(
        """SELECT t.*, a.name as animal_name, a.species
           FROM treatments t JOIN animals a ON t.animal_id = a.id
           WHERE t.withdrawal_end_date >= date('now')
           ORDER BY t.withdrawal_end_date"""
    )


# --- Medications ---

@router.get("/medications")
def list_medications() -> list[dict]:
    return query("SELECT * FROM medications ORDER BY name")


@router.post("/medications", status_code=201)
def create_medication(med: MedicationCreate) -> dict:
    mid = execute(
        """INSERT INTO medications (name, type, quantity, unit, low_threshold,
           default_withdrawal_days, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (med.name, med.type, med.quantity, med.unit, med.low_threshold,
         med.default_withdrawal_days, med.notes),
    )
    return query("SELECT * FROM medications WHERE id = ?", (mid,))[0]


@router.put("/medications/{med_id}")
def update_medication(med_id: int, med: MedicationUpdate) -> dict:
    existing = query("SELECT id FROM medications WHERE id = ?", (med_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Medication not found")
    updates: list[str] = []
    params: list = []
    for field in ["quantity", "low_threshold", "notes"]:
        value = getattr(med, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = datetime('now')")
    params.append(med_id)
    execute(
        f"UPDATE medications SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    return query("SELECT * FROM medications WHERE id = ?", (med_id,))[0]


@router.get("/medications/alerts")
def medication_alerts() -> list[dict]:
    """Return medications below their low threshold."""
    return query(
        "SELECT * FROM medications WHERE quantity <= low_threshold ORDER BY name"
    )


# --- Vaccinations ---

@router.get("/vaccinations")
def list_vaccinations(animal_id: Optional[int] = Query(None)) -> list[dict]:
    if animal_id:
        return query(
            """SELECT v.*, a.name as animal_name
               FROM vaccinations v JOIN animals a ON v.animal_id = a.id
               WHERE v.animal_id = ? ORDER BY v.date_given DESC""",
            (animal_id,),
        )
    return query(
        """SELECT v.*, a.name as animal_name
           FROM vaccinations v JOIN animals a ON v.animal_id = a.id
           ORDER BY v.date_given DESC"""
    )


@router.post("/vaccinations", status_code=201)
def create_vaccination(vax: VaccinationCreate) -> dict:
    animal = query("SELECT id FROM animals WHERE id = ?", (vax.animal_id,))
    if not animal:
        raise HTTPException(status_code=400, detail="Animal not found")
    vid = execute(
        """INSERT INTO vaccinations (animal_id, vaccine, date_given, next_due_date,
           administered_by, notes) VALUES (?, ?, ?, ?, ?, ?)""",
        (vax.animal_id, vax.vaccine, vax.date_given, vax.next_due_date,
         vax.administered_by, vax.notes),
    )
    return query(
        """SELECT v.*, a.name as animal_name
           FROM vaccinations v JOIN animals a ON v.animal_id = a.id
           WHERE v.id = ?""",
        (vid,),
    )[0]


@router.get("/vaccinations/due")
def vaccinations_due() -> list[dict]:
    """Return vaccinations that are due or overdue."""
    return query(
        """SELECT v.*, a.name as animal_name, a.species
           FROM vaccinations v JOIN animals a ON v.animal_id = a.id
           WHERE v.next_due_date <= date('now', '+30 days')
           AND v.next_due_date IS NOT NULL
           ORDER BY v.next_due_date"""
    )
