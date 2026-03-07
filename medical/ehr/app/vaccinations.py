"""Vaccination records endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/patients/{patient_id}/vaccinations", tags=["vaccinations"])


VACCINE_SCHEDULES: dict[str, list[dict]] = {
    "Tetanus/Diphtheria (Td)": [
        {"dose": 1, "age_months": 2},
        {"dose": 2, "age_months": 4},
        {"dose": 3, "age_months": 6},
        {"dose": 4, "age_months": 18},
        {"booster_interval_years": 10},
    ],
    "Measles/MMR": [
        {"dose": 1, "age_months": 12},
        {"dose": 2, "age_months": 48},
    ],
    "Hepatitis B": [
        {"dose": 1, "age_months": 0},
        {"dose": 2, "age_months": 1},
        {"dose": 3, "age_months": 6},
    ],
    "Polio (IPV/OPV)": [
        {"dose": 1, "age_months": 2},
        {"dose": 2, "age_months": 4},
        {"dose": 3, "age_months": 6},
        {"dose": 4, "age_months": 48},
    ],
    "Rabies (post-exposure)": [
        {"dose": 1, "day": 0},
        {"dose": 2, "day": 3},
        {"dose": 3, "day": 7},
        {"dose": 4, "day": 14},
    ],
}


class VaccinationCreate(BaseModel):
    vaccine_name: str
    date_administered: str
    lot_number: str = ""
    site: str = ""
    administered_by: str = ""
    next_dose_due: Optional[str] = None


def _check_patient(patient_id: int) -> None:
    if not query("SELECT id FROM patients WHERE id = ?", (patient_id,)):
        raise HTTPException(status_code=404, detail="Patient not found")


@router.get("")
def list_vaccinations(
    patient_id: int, user: str = Depends(require_medical_role),
) -> list[dict]:
    _check_patient(patient_id)
    log_action(user, "list", "vaccination", f"patient:{patient_id}")
    return query(
        "SELECT * FROM vaccinations WHERE patient_id = ? ORDER BY date_administered DESC",
        (patient_id,),
    )


@router.post("", status_code=201)
def create_vaccination(
    patient_id: int, vax: VaccinationCreate, user: str = Depends(require_medical_role),
) -> dict:
    _check_patient(patient_id)
    row_id = execute(
        """INSERT INTO vaccinations
           (patient_id, vaccine_name, date_administered, lot_number, site, administered_by, next_dose_due)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            patient_id, vax.vaccine_name, vax.date_administered,
            vax.lot_number, vax.site, vax.administered_by, vax.next_dose_due,
        ),
    )
    log_action(user, "create", "vaccination", str(row_id))
    return query("SELECT * FROM vaccinations WHERE id = ?", (row_id,))[0]


@router.get("/overdue")
def get_overdue_vaccinations(
    patient_id: int, user: str = Depends(require_medical_role),
) -> list[dict]:
    """Get vaccinations where next_dose_due is in the past."""
    _check_patient(patient_id)
    log_action(user, "list", "vaccination_overdue", f"patient:{patient_id}")
    return query(
        """SELECT * FROM vaccinations
           WHERE patient_id = ? AND next_dose_due IS NOT NULL AND next_dose_due < datetime('now')
           ORDER BY next_dose_due ASC""",
        (patient_id,),
    )


# Non-patient-scoped routes for schedules and coverage
schedule_router = APIRouter(prefix="/api/vaccinations", tags=["vaccinations"])


@schedule_router.get("/schedules")
def get_vaccine_schedules(_user: str = Depends(require_medical_role)) -> dict:
    return VACCINE_SCHEDULES


@schedule_router.get("/coverage")
def get_vaccination_coverage(
    vaccine_name: Optional[str] = Query(None),
    _user: str = Depends(require_medical_role),
) -> list[dict]:
    """Report vaccination coverage across all patients."""
    if vaccine_name:
        return query(
            """SELECT vaccine_name, COUNT(DISTINCT patient_id) as patients_vaccinated,
                      COUNT(*) as total_doses
               FROM vaccinations WHERE vaccine_name = ?
               GROUP BY vaccine_name""",
            (vaccine_name,),
        )
    return query(
        """SELECT vaccine_name, COUNT(DISTINCT patient_id) as patients_vaccinated,
                  COUNT(*) as total_doses
           FROM vaccinations GROUP BY vaccine_name ORDER BY vaccine_name""",
    )
