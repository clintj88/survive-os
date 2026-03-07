"""Animal records CRUD API."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/animals", tags=["animals"])


class AnimalCreate(BaseModel):
    name: str
    tag: Optional[str] = None
    species: str
    breed: str = ""
    sex: str = "unknown"
    birth_date: Optional[str] = None
    acquisition_date: Optional[str] = None
    sire_id: Optional[int] = None
    dam_id: Optional[int] = None
    status: str = "active"
    photo_path: Optional[str] = None
    notes: str = ""


class AnimalUpdate(BaseModel):
    name: Optional[str] = None
    tag: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    acquisition_date: Optional[str] = None
    sire_id: Optional[int] = None
    dam_id: Optional[int] = None
    status: Optional[str] = None
    photo_path: Optional[str] = None
    notes: Optional[str] = None


def _get_animal(animal_id: int) -> dict:
    results = query(
        "SELECT * FROM animals WHERE id = ?", (animal_id,)
    )
    if not results:
        raise HTTPException(status_code=404, detail="Animal not found")
    return results[0]


@router.get("")
def list_animals(
    species: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if species:
        conditions.append("species = ?")
        params.append(species)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(f"SELECT * FROM animals {where} ORDER BY name", tuple(params))


@router.get("/{animal_id}")
def get_animal(animal_id: int) -> dict:
    return _get_animal(animal_id)


@router.get("/{animal_id}/pedigree")
def get_pedigree(animal_id: int, depth: int = Query(3, ge=1, le=6)) -> dict:
    """Get pedigree tree for an animal up to specified depth."""
    animal = _get_animal(animal_id)
    return _build_pedigree(animal, depth)


def _build_pedigree(animal: dict, depth: int) -> dict:
    result = {
        "id": animal["id"],
        "name": animal["name"],
        "tag": animal["tag"],
        "species": animal["species"],
        "breed": animal["breed"],
        "sex": animal["sex"],
        "sire": None,
        "dam": None,
    }
    if depth <= 0:
        return result
    if animal.get("sire_id"):
        sire = query("SELECT * FROM animals WHERE id = ?", (animal["sire_id"],))
        if sire:
            result["sire"] = _build_pedigree(sire[0], depth - 1)
    if animal.get("dam_id"):
        dam = query("SELECT * FROM animals WHERE id = ?", (animal["dam_id"],))
        if dam:
            result["dam"] = _build_pedigree(dam[0], depth - 1)
    return result


@router.get("/{animal_id}/offspring")
def get_offspring(animal_id: int) -> list[dict]:
    _get_animal(animal_id)
    return query(
        "SELECT * FROM animals WHERE sire_id = ? OR dam_id = ? ORDER BY birth_date",
        (animal_id, animal_id),
    )


@router.post("", status_code=201)
def create_animal(animal: AnimalCreate) -> dict:
    if animal.sire_id:
        sire = query("SELECT id FROM animals WHERE id = ?", (animal.sire_id,))
        if not sire:
            raise HTTPException(status_code=400, detail="Sire not found")
    if animal.dam_id:
        dam = query("SELECT id FROM animals WHERE id = ?", (animal.dam_id,))
        if not dam:
            raise HTTPException(status_code=400, detail="Dam not found")
    animal_id = execute(
        """INSERT INTO animals (name, tag, species, breed, sex, birth_date,
           acquisition_date, sire_id, dam_id, status, photo_path, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            animal.name, animal.tag, animal.species, animal.breed, animal.sex,
            animal.birth_date, animal.acquisition_date, animal.sire_id,
            animal.dam_id, animal.status, animal.photo_path, animal.notes,
        ),
    )
    return _get_animal(animal_id)


@router.put("/{animal_id}")
def update_animal(animal_id: int, animal: AnimalUpdate) -> dict:
    _get_animal(animal_id)
    updates: list[str] = []
    params: list = []
    for field in [
        "name", "tag", "species", "breed", "sex", "birth_date",
        "acquisition_date", "sire_id", "dam_id", "status", "photo_path", "notes",
    ]:
        value = getattr(animal, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(animal_id)
    execute(f"UPDATE animals SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return _get_animal(animal_id)


@router.delete("/{animal_id}", status_code=204)
def delete_animal(animal_id: int) -> None:
    _get_animal(animal_id)
    execute("DELETE FROM animals WHERE id = ?", (animal_id,))
