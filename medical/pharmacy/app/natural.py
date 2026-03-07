"""Natural medicine reference routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/natural", tags=["natural-medicine"])


class NaturalMedicineCreate(BaseModel):
    name: str
    common_names: str = ""
    uses: str = ""
    preparation: str = ""
    dosage: str = ""
    contraindications: str = ""
    drug_interactions: str = ""
    habitat: str = ""
    identification: str = ""
    notes: str = ""


@router.get("")
def list_natural_medicines(
    search: Optional[str] = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    if search:
        return query(
            """SELECT * FROM natural_medicines
               WHERE name LIKE ? OR common_names LIKE ? OR uses LIKE ?
               ORDER BY name""",
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    return query("SELECT * FROM natural_medicines ORDER BY name")


@router.get("/{nm_id}")
def get_natural_medicine(
    nm_id: int,
    _role: str = Depends(require_medical_role),
) -> dict:
    results = query("SELECT * FROM natural_medicines WHERE id = ?", (nm_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Natural medicine not found")
    return results[0]


@router.post("", status_code=201)
def create_natural_medicine(
    nm: NaturalMedicineCreate,
    _role: str = Depends(require_medical_role),
) -> dict:
    nm_id = execute(
        """INSERT INTO natural_medicines
           (name, common_names, uses, preparation, dosage, contraindications,
            drug_interactions, habitat, identification, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (nm.name, nm.common_names, nm.uses, nm.preparation, nm.dosage,
         nm.contraindications, nm.drug_interactions, nm.habitat, nm.identification, nm.notes),
    )
    return query("SELECT * FROM natural_medicines WHERE id = ?", (nm_id,))[0]
