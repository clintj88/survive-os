"""Dosage calculator routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import query

router = APIRouter(prefix="/api/dosage", tags=["dosage"])


class DoseCalcRequest(BaseModel):
    medication: str
    weight_kg: float
    age_months: int


@router.get("/rules")
def list_dosing_rules(
    medication: str | None = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    if medication:
        return query(
            "SELECT * FROM dosing_rules WHERE LOWER(medication_name) = LOWER(?) ORDER BY age_min_months",
            (medication,),
        )
    return query("SELECT * FROM dosing_rules ORDER BY medication_name, age_min_months")


@router.post("/calculate")
def calculate_dose(
    req: DoseCalcRequest,
    _role: str = Depends(require_medical_role),
) -> dict:
    """Calculate recommended dose based on weight and age."""
    rules = query(
        """SELECT * FROM dosing_rules
           WHERE LOWER(medication_name) = LOWER(?)
             AND age_min_months <= ? AND age_max_months >= ?
           ORDER BY age_min_months""",
        (req.medication, req.age_months, req.age_months),
    )
    if not rules:
        raise HTTPException(
            status_code=404,
            detail=f"No dosing rules found for {req.medication} at age {req.age_months} months",
        )

    rule = rules[0]
    calculated_dose = req.weight_kg * rule["dose_mg_per_kg"]

    # Cap at max single dose if set
    if rule["max_single_dose_mg"] > 0:
        calculated_dose = min(calculated_dose, rule["max_single_dose_mg"])

    # For adults (age >= 216 months / 18 years), use adult dose if available
    if req.age_months >= 216 and rule["adult_dose_mg"] > 0:
        calculated_dose = rule["adult_dose_mg"]

    doses_per_day = 24 / rule["frequency_hours"] if rule["frequency_hours"] > 0 else 1
    daily_total = calculated_dose * doses_per_day

    # Cap at max daily dose
    if rule["max_daily_dose_mg"] > 0 and daily_total > rule["max_daily_dose_mg"]:
        calculated_dose = rule["max_daily_dose_mg"] / doses_per_day
        daily_total = rule["max_daily_dose_mg"]

    return {
        "medication": req.medication,
        "weight_kg": req.weight_kg,
        "age_months": req.age_months,
        "recommended_dose_mg": round(calculated_dose, 1),
        "frequency_hours": rule["frequency_hours"],
        "max_single_dose_mg": rule["max_single_dose_mg"],
        "max_daily_dose_mg": rule["max_daily_dose_mg"],
        "calculated_daily_total_mg": round(daily_total, 1),
        "indication": rule["indication"],
        "notes": rule["notes"],
    }
