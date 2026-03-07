"""Drug interaction checker routes."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import query

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


class InteractionCheckRequest(BaseModel):
    medications: list[str]


class InteractionCheckWithPatientRequest(BaseModel):
    patient_id: str
    new_medication: str


@router.get("")
def list_interactions(
    severity: str | None = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    if severity:
        return query(
            "SELECT * FROM drug_interactions WHERE severity = ? ORDER BY drug_a, drug_b",
            (severity,),
        )
    return query("SELECT * FROM drug_interactions ORDER BY severity DESC, drug_a, drug_b")


@router.post("/check")
def check_interactions(
    req: InteractionCheckRequest,
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    """Check for interactions between a list of medications."""
    if len(req.medications) < 2:
        return []

    found: list[dict] = []
    meds_lower = [m.lower() for m in req.medications]

    for i, drug_a in enumerate(meds_lower):
        for drug_b in meds_lower[i + 1:]:
            results = query(
                """SELECT * FROM drug_interactions
                   WHERE (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                      OR (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)""",
                (drug_a, drug_b, drug_b, drug_a),
            )
            found.extend(results)

    # Sort by severity (contraindicated > major > moderate > minor)
    severity_order = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}
    found.sort(key=lambda x: severity_order.get(x["severity"], 4))
    return found


@router.post("/check-patient")
def check_patient_interactions(
    req: InteractionCheckWithPatientRequest,
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    """Check if a new medication interacts with a patient's active prescriptions."""
    active_meds = query(
        """SELECT DISTINCT m.name
           FROM prescriptions p
           JOIN medications m ON p.medication_id = m.id
           WHERE p.patient_id = ? AND p.status = 'active'""",
        (req.patient_id,),
    )
    med_names = [m["name"] for m in active_meds] + [req.new_medication]
    check_req = InteractionCheckRequest(medications=med_names)
    return check_interactions(check_req)
