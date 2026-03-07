"""Breeding planner and inbreeding coefficient calculator."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/breeding", tags=["breeding"])

# Gestation periods in days by species
GESTATION_DAYS: dict[str, int] = {
    "cattle": 283,
    "goat": 150,
    "sheep": 152,
    "pig": 114,
    "chicken": 21,
    "horse": 340,
    "rabbit": 31,
    "duck": 28,
    "turkey": 28,
}


class BreedingEventCreate(BaseModel):
    sire_id: int
    dam_id: int
    date_bred: str
    expected_due_date: Optional[str] = None
    notes: str = ""


class BreedingEventUpdate(BaseModel):
    actual_due_date: Optional[str] = None
    outcome: Optional[str] = None
    offspring_count: Optional[int] = None
    notes: Optional[str] = None


@router.get("/events")
def list_breeding_events(
    status: Optional[str] = Query(None),
) -> list[dict]:
    if status:
        return query(
            """SELECT b.*, s.name as sire_name, d.name as dam_name
               FROM breeding_events b
               JOIN animals s ON b.sire_id = s.id
               JOIN animals d ON b.dam_id = d.id
               WHERE b.outcome = ? ORDER BY b.date_bred DESC""",
            (status,),
        )
    return query(
        """SELECT b.*, s.name as sire_name, d.name as dam_name
           FROM breeding_events b
           JOIN animals s ON b.sire_id = s.id
           JOIN animals d ON b.dam_id = d.id
           ORDER BY b.date_bred DESC"""
    )


@router.get("/events/{event_id}")
def get_breeding_event(event_id: int) -> dict:
    results = query(
        """SELECT b.*, s.name as sire_name, d.name as dam_name
           FROM breeding_events b
           JOIN animals s ON b.sire_id = s.id
           JOIN animals d ON b.dam_id = d.id
           WHERE b.id = ?""",
        (event_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Breeding event not found")
    return results[0]


@router.post("/events", status_code=201)
def create_breeding_event(event: BreedingEventCreate) -> dict:
    sire = query("SELECT * FROM animals WHERE id = ?", (event.sire_id,))
    if not sire:
        raise HTTPException(status_code=400, detail="Sire not found")
    dam = query("SELECT * FROM animals WHERE id = ?", (event.dam_id,))
    if not dam:
        raise HTTPException(status_code=400, detail="Dam not found")

    expected_due = event.expected_due_date
    if not expected_due:
        species = dam[0]["species"].lower()
        gestation = GESTATION_DAYS.get(species, 150)
        bred_date = datetime.strptime(event.date_bred, "%Y-%m-%d")
        expected_due = (bred_date + timedelta(days=gestation)).strftime("%Y-%m-%d")

    event_id = execute(
        """INSERT INTO breeding_events (sire_id, dam_id, date_bred, expected_due_date, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (event.sire_id, event.dam_id, event.date_bred, expected_due, event.notes),
    )
    return get_breeding_event(event_id)


@router.put("/events/{event_id}")
def update_breeding_event(event_id: int, event: BreedingEventUpdate) -> dict:
    existing = query("SELECT id FROM breeding_events WHERE id = ?", (event_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Breeding event not found")
    updates: list[str] = []
    params: list = []
    for field in ["actual_due_date", "outcome", "offspring_count", "notes"]:
        value = getattr(event, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(event_id)
    execute(
        f"UPDATE breeding_events SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    return get_breeding_event(event_id)


@router.get("/gestation")
def get_gestation_periods() -> dict[str, int]:
    return GESTATION_DAYS


@router.get("/gestation/{species}")
def calculate_due_date(species: str, date_bred: str = Query(...)) -> dict:
    gestation = GESTATION_DAYS.get(species.lower())
    if gestation is None:
        raise HTTPException(status_code=404, detail=f"Unknown species: {species}")
    bred_date = datetime.strptime(date_bred, "%Y-%m-%d")
    due_date = bred_date + timedelta(days=gestation)
    return {
        "species": species.lower(),
        "date_bred": date_bred,
        "gestation_days": gestation,
        "expected_due_date": due_date.strftime("%Y-%m-%d"),
    }


def _get_ancestors(animal_id: int, depth: int) -> dict[int, list[list[int]]]:
    """Build a map of ancestor_id -> list of paths from animal to ancestor.

    Each path is a list of ancestor IDs traversed. Used for Wright's
    coefficient of inbreeding calculation.
    """
    ancestors: dict[int, list[list[int]]] = {}

    def _walk(current_id: int, path: list[int], remaining: int) -> None:
        if remaining <= 0:
            return
        animal = query(
            "SELECT sire_id, dam_id FROM animals WHERE id = ?", (current_id,)
        )
        if not animal:
            return
        for parent_id in [animal[0]["sire_id"], animal[0]["dam_id"]]:
            if parent_id is None:
                continue
            new_path = path + [parent_id]
            if parent_id not in ancestors:
                ancestors[parent_id] = []
            ancestors[parent_id].append(new_path)
            _walk(parent_id, new_path, remaining - 1)

    _walk(animal_id, [], depth)
    return ancestors


def calculate_inbreeding_coefficient(
    sire_id: int, dam_id: int, max_depth: int = 6
) -> float:
    """Calculate Wright's coefficient of inbreeding for potential offspring.

    F = sum over common ancestors A of: (1/2)^(n1+n2+1) * (1 + F_A)

    Where n1 = generations from sire to common ancestor A,
          n2 = generations from dam to common ancestor A,
          F_A = inbreeding coefficient of ancestor A (assumed 0 for simplicity).
    """
    sire_ancestors = _get_ancestors(sire_id, max_depth)
    dam_ancestors = _get_ancestors(dam_id, max_depth)

    common = set(sire_ancestors.keys()) & set(dam_ancestors.keys())
    if not common:
        return 0.0

    f = 0.0
    for ancestor_id in common:
        for sire_path in sire_ancestors[ancestor_id]:
            for dam_path in dam_ancestors[ancestor_id]:
                n1 = len(sire_path)
                n2 = len(dam_path)
                f += (0.5) ** (n1 + n2 + 1)
    return round(f, 6)


@router.get("/inbreeding")
def check_inbreeding(
    sire_id: int = Query(...),
    dam_id: int = Query(...),
) -> dict:
    """Calculate inbreeding coefficient for a potential mating."""
    sire = query("SELECT * FROM animals WHERE id = ?", (sire_id,))
    if not sire:
        raise HTTPException(status_code=400, detail="Sire not found")
    dam = query("SELECT * FROM animals WHERE id = ?", (dam_id,))
    if not dam:
        raise HTTPException(status_code=400, detail="Dam not found")

    coefficient = calculate_inbreeding_coefficient(sire_id, dam_id)
    from .config import load_config
    threshold = load_config()["breeding"]["inbreeding_threshold"]

    return {
        "sire_id": sire_id,
        "sire_name": sire[0]["name"],
        "dam_id": dam_id,
        "dam_name": dam[0]["name"],
        "coefficient": coefficient,
        "threshold": threshold,
        "warning": coefficient >= threshold,
    }


@router.get("/suggestions")
def suggest_pairings(species: Optional[str] = Query(None)) -> list[dict]:
    """Suggest optimal pairings that minimize inbreeding."""
    conditions = "WHERE status = 'active'"
    params: list = []
    if species:
        conditions += " AND species = ?"
        params.append(species)

    males = query(
        f"SELECT * FROM animals {conditions} AND sex = 'male'", tuple(params)
    )
    females = query(
        f"SELECT * FROM animals {conditions} AND sex = 'female'", tuple(params)
    )

    pairings: list[dict] = []
    for male in males:
        for female in females:
            coeff = calculate_inbreeding_coefficient(male["id"], female["id"])
            from .config import load_config
            threshold = load_config()["breeding"]["inbreeding_threshold"]
            pairings.append({
                "sire_id": male["id"],
                "sire_name": male["name"],
                "dam_id": female["id"],
                "dam_name": female["name"],
                "coefficient": coeff,
                "warning": coeff >= threshold,
            })

    pairings.sort(key=lambda p: p["coefficient"])
    return pairings
