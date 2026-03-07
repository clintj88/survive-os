"""Veterinary (Livestock) API routes.

Cross-links to agriculture/livestock module for animal details.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .config import load_config
from .database import execute, query
from seed.vet_conditions import CONDITIONS, TREATMENT_PROTOCOLS

router = APIRouter(prefix="/api/vet", tags=["veterinary"])


class VetVisitCreate(BaseModel):
    animal_id: str
    visit_date: Optional[str] = None
    condition: str
    treatment: str = ""
    provider: str = ""
    notes: str = ""


@router.get("/visits")
def list_visits(animal_id: Optional[str] = None,
                _role: str = Depends(require_medical_role)) -> list[dict]:
    if animal_id:
        return query(
            "SELECT * FROM vet_visits WHERE animal_id = ? ORDER BY visit_date DESC",
            (animal_id,),
        )
    return query("SELECT * FROM vet_visits ORDER BY visit_date DESC")


@router.get("/visits/{visit_id}")
def get_visit(visit_id: int, _role: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM vet_visits WHERE id = ?", (visit_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Visit not found")
    return rows[0]


@router.post("/visits", status_code=201)
def create_visit(data: VetVisitCreate, _role: str = Depends(require_medical_role)) -> dict:
    vid = execute(
        """INSERT INTO vet_visits (animal_id, visit_date, condition, treatment, provider, notes)
           VALUES (?, COALESCE(?, datetime('now')), ?, ?, ?, ?)""",
        (data.animal_id, data.visit_date, data.condition, data.treatment,
         data.provider, data.notes),
    )
    rows = query("SELECT * FROM vet_visits WHERE id = ?", (vid,))
    return rows[0]


@router.get("/herd-health")
def herd_health_report(_role: str = Depends(require_medical_role)) -> dict:
    """Aggregate condition tracking across all animals."""
    total_visits = query("SELECT COUNT(*) as count FROM vet_visits")
    unique_animals = query("SELECT COUNT(DISTINCT animal_id) as count FROM vet_visits")
    conditions_breakdown = query(
        """SELECT condition, COUNT(*) as count FROM vet_visits
           GROUP BY condition ORDER BY count DESC"""
    )
    recent_visits = query(
        "SELECT * FROM vet_visits ORDER BY visit_date DESC LIMIT 10"
    )
    return {
        "total_visits": total_visits[0]["count"] if total_visits else 0,
        "unique_animals": unique_animals[0]["count"] if unique_animals else 0,
        "conditions": conditions_breakdown,
        "recent_visits": recent_visits,
    }


@router.get("/conditions")
def list_conditions(_role: str = Depends(require_medical_role)) -> list[dict]:
    return CONDITIONS


@router.get("/protocols")
def list_protocols(_role: str = Depends(require_medical_role)) -> list[dict]:
    return TREATMENT_PROTOCOLS


@router.get("/animals/{animal_id}")
def get_animal_info(animal_id: str, _role: str = Depends(require_medical_role)) -> dict:
    """Query agriculture livestock module for animal details.
    Falls back to local visit data if agriculture module is unavailable.
    """
    visits = query(
        "SELECT * FROM vet_visits WHERE animal_id = ? ORDER BY visit_date DESC",
        (animal_id,),
    )
    config = load_config()
    ag_url = config["agriculture_api"]["url"]

    animal_info: dict = {"animal_id": animal_id, "source": "local"}

    try:
        import httpx
        resp = httpx.get(f"{ag_url}/api/animals/{animal_id}", timeout=5.0)
        if resp.status_code == 200:
            animal_info = resp.json()
            animal_info["source"] = "agriculture"
    except Exception:
        pass

    animal_info["vet_visits"] = visits
    return animal_info
