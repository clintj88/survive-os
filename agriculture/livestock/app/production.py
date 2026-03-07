"""Production records and analytics."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/production", tags=["production"])


class ProductionRecordCreate(BaseModel):
    animal_id: int
    type: str
    value: float
    unit: str
    date: Optional[str] = None
    notes: str = ""


@router.get("/records")
def list_records(
    animal_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if animal_id:
        conditions.append("p.animal_id = ?")
        params.append(animal_id)
    if type:
        conditions.append("p.type = ?")
        params.append(type)
    if start_date:
        conditions.append("p.date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("p.date <= ?")
        params.append(end_date)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT p.*, a.name as animal_name
            FROM production_records p JOIN animals a ON p.animal_id = a.id
            {where} ORDER BY p.date DESC""",
        tuple(params),
    )


@router.post("/records", status_code=201)
def create_record(record: ProductionRecordCreate) -> dict:
    animal = query("SELECT id FROM animals WHERE id = ?", (record.animal_id,))
    if not animal:
        raise HTTPException(status_code=400, detail="Animal not found")

    date = record.date
    if not date:
        from datetime import date as dt_date
        date = dt_date.today().isoformat()

    rid = execute(
        """INSERT INTO production_records (animal_id, type, value, unit, date, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (record.animal_id, record.type, record.value, record.unit, date, record.notes),
    )
    return query(
        """SELECT p.*, a.name as animal_name
           FROM production_records p JOIN animals a ON p.animal_id = a.id
           WHERE p.id = ?""",
        (rid,),
    )[0]


@router.get("/analytics")
def production_analytics(
    type: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
) -> dict:
    """Get production analytics: averages, totals, top producers."""
    conditions = ["p.type = ?"]
    params: list = [type]
    if start_date:
        conditions.append("p.date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("p.date <= ?")
        params.append(end_date)
    where = f"WHERE {' AND '.join(conditions)}"

    # Overall stats
    stats = query(
        f"""SELECT COUNT(*) as count, AVG(p.value) as avg_value,
                   SUM(p.value) as total, MIN(p.value) as min_value,
                   MAX(p.value) as max_value
            FROM production_records p {where}""",
        tuple(params),
    )

    # Per-animal stats (top producers)
    top = query(
        f"""SELECT a.id, a.name, a.species,
                   COUNT(p.id) as record_count,
                   AVG(p.value) as avg_value,
                   SUM(p.value) as total_value
            FROM production_records p
            JOIN animals a ON p.animal_id = a.id
            {where}
            GROUP BY a.id
            ORDER BY total_value DESC
            LIMIT 10""",
        tuple(params),
    )

    # Daily totals
    daily = query(
        f"""SELECT p.date, SUM(p.value) as total, COUNT(p.id) as count
            FROM production_records p
            {where}
            GROUP BY p.date
            ORDER BY p.date DESC
            LIMIT 30""",
        tuple(params),
    )

    return {
        "type": type,
        "summary": stats[0] if stats else {},
        "top_producers": [dict(t) for t in top],
        "daily_totals": [dict(d) for d in daily],
    }


@router.get("/fcr")
def feed_conversion_ratio(
    animal_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
) -> dict:
    """Calculate feed conversion ratio (feed consumed / weight gained)."""
    conditions_feed = ["fc.animal_id = ?"]
    conditions_weight = ["p.animal_id = ?", "p.type = 'weight'"]
    params_feed: list = [animal_id]
    params_weight: list = [animal_id]

    if start_date:
        conditions_feed.append("fc.date >= ?")
        params_feed.append(start_date)
        conditions_weight.append("p.date >= ?")
        params_weight.append(start_date)
    if end_date:
        conditions_feed.append("fc.date <= ?")
        params_feed.append(end_date)
        conditions_weight.append("p.date <= ?")
        params_weight.append(end_date)

    where_feed = " AND ".join(conditions_feed)
    where_weight = " AND ".join(conditions_weight)

    feed = query(
        f"SELECT SUM(quantity) as total_feed FROM feed_consumption fc WHERE {where_feed}",
        tuple(params_feed),
    )
    weights = query(
        f"""SELECT MIN(p.value) as min_weight, MAX(p.value) as max_weight
            FROM production_records p WHERE {where_weight}""",
        tuple(params_weight),
    )

    total_feed = feed[0]["total_feed"] if feed and feed[0]["total_feed"] else 0
    min_w = weights[0]["min_weight"] if weights and weights[0]["min_weight"] else 0
    max_w = weights[0]["max_weight"] if weights and weights[0]["max_weight"] else 0
    weight_gain = max_w - min_w

    fcr = round(total_feed / weight_gain, 2) if weight_gain > 0 else None

    animal = query("SELECT name FROM animals WHERE id = ?", (animal_id,))
    return {
        "animal_id": animal_id,
        "animal_name": animal[0]["name"] if animal else "Unknown",
        "total_feed_kg": round(total_feed, 2),
        "weight_gain_kg": round(weight_gain, 2),
        "fcr": fcr,
    }
