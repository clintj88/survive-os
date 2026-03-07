"""Feed requirements calculator and inventory tracking."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/feed", tags=["feed"])


class FeedTypeCreate(BaseModel):
    name: str
    unit: str = "kg"
    calories_per_unit: float = 0
    protein_pct: float = 0
    notes: str = ""


class FeedInventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    low_threshold: Optional[float] = None


class FeedConsumptionCreate(BaseModel):
    animal_id: int
    feed_type_id: int
    quantity: float
    date: Optional[str] = None


# --- Feed types ---

@router.get("/types")
def list_feed_types() -> list[dict]:
    return query("SELECT * FROM feed_types ORDER BY name")


@router.post("/types", status_code=201)
def create_feed_type(feed: FeedTypeCreate) -> dict:
    fid = execute(
        "INSERT INTO feed_types (name, unit, calories_per_unit, protein_pct, notes) VALUES (?, ?, ?, ?, ?)",
        (feed.name, feed.unit, feed.calories_per_unit, feed.protein_pct, feed.notes),
    )
    return query("SELECT * FROM feed_types WHERE id = ?", (fid,))[0]


# --- Feed requirements ---

@router.get("/requirements")
def list_feed_requirements(species: Optional[str] = Query(None)) -> list[dict]:
    if species:
        return query(
            "SELECT * FROM feed_requirements WHERE species = ? ORDER BY production_stage, min_weight_kg",
            (species.lower(),),
        )
    return query("SELECT * FROM feed_requirements ORDER BY species, production_stage, min_weight_kg")


@router.get("/calculate")
def calculate_feed(
    species: str = Query(...),
    weight_kg: float = Query(..., gt=0),
    production_stage: str = Query("maintenance"),
) -> dict:
    """Calculate daily feed requirement for an animal."""
    reqs = query(
        """SELECT * FROM feed_requirements
           WHERE species = ? AND production_stage = ?
           AND min_weight_kg <= ? AND max_weight_kg >= ?
           LIMIT 1""",
        (species.lower(), production_stage, weight_kg, weight_kg),
    )
    if not reqs:
        reqs = query(
            """SELECT * FROM feed_requirements
               WHERE species = ? AND production_stage = ?
               ORDER BY ABS(min_weight_kg - ?) LIMIT 1""",
            (species.lower(), production_stage, weight_kg),
        )
    if not reqs:
        raise HTTPException(
            status_code=404,
            detail=f"No feed data for {species}/{production_stage}",
        )
    req = reqs[0]
    daily_dm_kg = weight_kg * (req["daily_dm_pct_bw"] / 100)
    daily_protein_kg = daily_dm_kg * (req["crude_protein_pct"] / 100)

    return {
        "species": species.lower(),
        "weight_kg": weight_kg,
        "production_stage": production_stage,
        "daily_dry_matter_kg": round(daily_dm_kg, 2),
        "daily_crude_protein_kg": round(daily_protein_kg, 2),
        "dm_pct_body_weight": req["daily_dm_pct_bw"],
        "crude_protein_pct": req["crude_protein_pct"],
        "notes": req["notes"],
    }


# --- Feed inventory ---

@router.get("/inventory")
def list_feed_inventory() -> list[dict]:
    return query(
        """SELECT fi.*, ft.name as feed_name, ft.unit
           FROM feed_inventory fi
           JOIN feed_types ft ON fi.feed_type_id = ft.id
           ORDER BY ft.name"""
    )


@router.get("/inventory/alerts")
def feed_alerts() -> list[dict]:
    """Return feed items that are below their low threshold."""
    return query(
        """SELECT fi.*, ft.name as feed_name, ft.unit
           FROM feed_inventory fi
           JOIN feed_types ft ON fi.feed_type_id = ft.id
           WHERE fi.quantity <= fi.low_threshold
           ORDER BY ft.name"""
    )


@router.post("/inventory", status_code=201)
def create_feed_inventory(feed_type_id: int, quantity: float = 0, low_threshold: float = 10) -> dict:
    ft = query("SELECT id FROM feed_types WHERE id = ?", (feed_type_id,))
    if not ft:
        raise HTTPException(status_code=400, detail="Feed type not found")
    fid = execute(
        "INSERT INTO feed_inventory (feed_type_id, quantity, low_threshold) VALUES (?, ?, ?)",
        (feed_type_id, quantity, low_threshold),
    )
    return query(
        """SELECT fi.*, ft.name as feed_name, ft.unit
           FROM feed_inventory fi JOIN feed_types ft ON fi.feed_type_id = ft.id
           WHERE fi.id = ?""",
        (fid,),
    )[0]


@router.put("/inventory/{inventory_id}")
def update_feed_inventory(inventory_id: int, update: FeedInventoryUpdate) -> dict:
    existing = query("SELECT id FROM feed_inventory WHERE id = ?", (inventory_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    updates: list[str] = []
    params: list = []
    if update.quantity is not None:
        updates.append("quantity = ?")
        params.append(update.quantity)
    if update.low_threshold is not None:
        updates.append("low_threshold = ?")
        params.append(update.low_threshold)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = datetime('now')")
    params.append(inventory_id)
    execute(
        f"UPDATE feed_inventory SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    return query(
        """SELECT fi.*, ft.name as feed_name, ft.unit
           FROM feed_inventory fi JOIN feed_types ft ON fi.feed_type_id = ft.id
           WHERE fi.id = ?""",
        (inventory_id,),
    )[0]


# --- Feed consumption ---

@router.get("/consumption")
def list_consumption(
    animal_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if animal_id:
        conditions.append("fc.animal_id = ?")
        params.append(animal_id)
    if date:
        conditions.append("fc.date = ?")
        params.append(date)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT fc.*, a.name as animal_name, ft.name as feed_name, ft.unit
            FROM feed_consumption fc
            JOIN animals a ON fc.animal_id = a.id
            JOIN feed_types ft ON fc.feed_type_id = ft.id
            {where} ORDER BY fc.date DESC""",
        tuple(params),
    )


@router.post("/consumption", status_code=201)
def record_consumption(record: FeedConsumptionCreate) -> dict:
    animal = query("SELECT id FROM animals WHERE id = ?", (record.animal_id,))
    if not animal:
        raise HTTPException(status_code=400, detail="Animal not found")
    ft = query("SELECT id FROM feed_types WHERE id = ?", (record.feed_type_id,))
    if not ft:
        raise HTTPException(status_code=400, detail="Feed type not found")

    date = record.date or "date('now')"
    fid = execute(
        "INSERT INTO feed_consumption (animal_id, feed_type_id, quantity, date) VALUES (?, ?, ?, ?)",
        (record.animal_id, record.feed_type_id, record.quantity, record.date or datetime_today()),
    )

    # Deduct from inventory
    inv = query(
        "SELECT * FROM feed_inventory WHERE feed_type_id = ?", (record.feed_type_id,)
    )
    if inv:
        new_qty = max(0, inv[0]["quantity"] - record.quantity)
        execute(
            "UPDATE feed_inventory SET quantity = ?, updated_at = datetime('now') WHERE id = ?",
            (new_qty, inv[0]["id"]),
        )

    return query(
        """SELECT fc.*, a.name as animal_name, ft.name as feed_name, ft.unit
           FROM feed_consumption fc
           JOIN animals a ON fc.animal_id = a.id
           JOIN feed_types ft ON fc.feed_type_id = ft.id
           WHERE fc.id = ?""",
        (fid,),
    )[0]


def datetime_today() -> str:
    from datetime import date
    return date.today().isoformat()
