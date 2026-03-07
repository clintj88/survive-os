"""Fuel reserves tracking API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/fuel", tags=["fuel"])


class FuelStorageCreate(BaseModel):
    fuel_type: str
    quantity: float
    unit: str
    storage_location: str = ""
    date_added: Optional[str] = None


class FuelConsumptionLog(BaseModel):
    fuel_type: str
    quantity_used: float
    unit: str
    purpose: str = ""
    date: Optional[str] = None
    used_by: str = ""


@router.get("/storage")
def list_storage(
    fuel_type: Optional[str] = Query(None),
) -> list[dict]:
    if fuel_type:
        return query(
            "SELECT * FROM fuel_storage WHERE fuel_type = ? ORDER BY date_added DESC",
            (fuel_type,),
        )
    return query("SELECT * FROM fuel_storage ORDER BY fuel_type, date_added DESC")


@router.post("/storage", status_code=201)
def add_fuel(entry: FuelStorageCreate) -> dict:
    if entry.date_added:
        row_id = execute(
            """INSERT INTO fuel_storage (fuel_type, quantity, unit, storage_location,
               date_added) VALUES (?, ?, ?, ?, ?)""",
            (entry.fuel_type, entry.quantity, entry.unit,
             entry.storage_location, entry.date_added),
        )
    else:
        row_id = execute(
            """INSERT INTO fuel_storage (fuel_type, quantity, unit, storage_location)
               VALUES (?, ?, ?, ?)""",
            (entry.fuel_type, entry.quantity, entry.unit, entry.storage_location),
        )
    results = query("SELECT * FROM fuel_storage WHERE id = ?", (row_id,))
    return results[0]


@router.delete("/storage/{entry_id}", status_code=204)
def delete_storage(entry_id: int) -> None:
    existing = query("SELECT id FROM fuel_storage WHERE id = ?", (entry_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Fuel storage entry not found")
    execute("DELETE FROM fuel_storage WHERE id = ?", (entry_id,))


@router.get("/consumption")
def list_consumption(
    fuel_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    if fuel_type:
        return query(
            "SELECT * FROM fuel_consumption WHERE fuel_type = ? ORDER BY date DESC LIMIT ?",
            (fuel_type, limit),
        )
    return query("SELECT * FROM fuel_consumption ORDER BY date DESC LIMIT ?", (limit,))


@router.post("/consumption", status_code=201)
def log_consumption(entry: FuelConsumptionLog) -> dict:
    if entry.date:
        row_id = execute(
            """INSERT INTO fuel_consumption (fuel_type, quantity_used, unit, purpose,
               date, used_by) VALUES (?, ?, ?, ?, ?, ?)""",
            (entry.fuel_type, entry.quantity_used, entry.unit,
             entry.purpose, entry.date, entry.used_by),
        )
    else:
        row_id = execute(
            """INSERT INTO fuel_consumption (fuel_type, quantity_used, unit, purpose,
               used_by) VALUES (?, ?, ?, ?, ?)""",
            (entry.fuel_type, entry.quantity_used, entry.unit,
             entry.purpose, entry.used_by),
        )
    results = query("SELECT * FROM fuel_consumption WHERE id = ?", (row_id,))
    return results[0]


@router.get("/summary")
def fuel_summary() -> list[dict]:
    fuel_types = ["gasoline", "diesel", "propane", "firewood", "kerosene", "ethanol"]
    result = []
    for ft in fuel_types:
        storage = query(
            "SELECT SUM(quantity) as total, unit FROM fuel_storage WHERE fuel_type = ? GROUP BY unit",
            (ft,),
        )
        consumed = query(
            "SELECT SUM(quantity_used) as total, unit FROM fuel_consumption WHERE fuel_type = ? GROUP BY unit",
            (ft,),
        )

        total_stored = storage[0]["total"] if storage and storage[0]["total"] else 0
        unit = storage[0]["unit"] if storage else "liters"
        total_consumed = consumed[0]["total"] if consumed and consumed[0]["total"] else 0

        net = max(0, total_stored - total_consumed)

        result.append({
            "fuel_type": ft,
            "total_stored": round(total_stored, 2),
            "total_consumed": round(total_consumed, 2),
            "net_available": round(net, 2),
            "unit": unit,
        })
    return result


@router.get("/days-of-supply")
def days_of_supply() -> list[dict]:
    fuel_types = ["gasoline", "diesel", "propane", "firewood", "kerosene", "ethanol"]
    result = []
    for ft in fuel_types:
        storage = query(
            "SELECT SUM(quantity) as total, unit FROM fuel_storage WHERE fuel_type = ? GROUP BY unit",
            (ft,),
        )
        total_stored = storage[0]["total"] if storage and storage[0]["total"] else 0
        unit = storage[0]["unit"] if storage else "liters"

        consumed = query(
            "SELECT SUM(quantity_used) as total FROM fuel_consumption WHERE fuel_type = ?",
            (ft,),
        )
        total_consumed = consumed[0]["total"] if consumed and consumed[0]["total"] else 0
        net = max(0, total_stored - total_consumed)

        # Calculate average daily consumption over last 30 days
        daily_avg = query(
            """SELECT AVG(daily_total) as avg_daily FROM (
                SELECT date, SUM(quantity_used) as daily_total
                FROM fuel_consumption WHERE fuel_type = ?
                AND date >= date('now', '-30 days')
                GROUP BY date
            )""",
            (ft,),
        )
        avg_daily = daily_avg[0]["avg_daily"] if daily_avg and daily_avg[0]["avg_daily"] else 0

        days = round(net / avg_daily, 1) if avg_daily > 0 else -1

        result.append({
            "fuel_type": ft,
            "net_available": round(net, 2),
            "unit": unit,
            "avg_daily_consumption": round(avg_daily, 2),
            "days_of_supply": days,
        })
    return result


@router.get("/low-fuel")
def low_fuel_alerts(
    threshold_days: int = Query(7, ge=1),
) -> list[dict]:
    supply = days_of_supply()
    return [
        s for s in supply
        if s["days_of_supply"] >= 0 and s["days_of_supply"] <= threshold_days
    ]
