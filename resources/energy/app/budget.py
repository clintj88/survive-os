"""Power budget calculator API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/budget", tags=["budget"])


class LoadCreate(BaseModel):
    name: str
    watts_draw: float
    priority: str = "optional"
    hours_per_day: float = 0.0


class LoadUpdate(BaseModel):
    name: Optional[str] = None
    watts_draw: Optional[float] = None
    priority: Optional[str] = None
    hours_per_day: Optional[float] = None


@router.get("/loads")
def list_loads(
    priority: Optional[str] = Query(None),
) -> list[dict]:
    if priority:
        return query(
            "SELECT * FROM power_loads WHERE priority = ? ORDER BY name",
            (priority,),
        )
    return query("SELECT * FROM power_loads ORDER BY priority, name")


@router.post("/loads", status_code=201)
def create_load(load: LoadCreate) -> dict:
    load_id = execute(
        "INSERT INTO power_loads (name, watts_draw, priority, hours_per_day) VALUES (?, ?, ?, ?)",
        (load.name, load.watts_draw, load.priority, load.hours_per_day),
    )
    results = query("SELECT * FROM power_loads WHERE id = ?", (load_id,))
    return results[0]


@router.get("/loads/{load_id}")
def get_load(load_id: int) -> dict:
    results = query("SELECT * FROM power_loads WHERE id = ?", (load_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Load not found")
    return results[0]


@router.put("/loads/{load_id}")
def update_load(load_id: int, load: LoadUpdate) -> dict:
    existing = query("SELECT id FROM power_loads WHERE id = ?", (load_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Load not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "watts_draw", "priority", "hours_per_day"]:
        value = getattr(load, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(load_id)
    execute(f"UPDATE power_loads SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_load(load_id)


@router.delete("/loads/{load_id}", status_code=204)
def delete_load(load_id: int) -> None:
    existing = query("SELECT id FROM power_loads WHERE id = ?", (load_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Load not found")
    execute("DELETE FROM power_loads WHERE id = ?", (load_id,))


@router.get("/demand")
def calculate_demand() -> dict:
    loads = query("SELECT * FROM power_loads ORDER BY priority, name")

    total_wh = 0
    by_priority: dict[str, float] = {"critical": 0, "important": 0, "optional": 0}
    breakdown = []

    for load in loads:
        wh = load["watts_draw"] * load["hours_per_day"]
        total_wh += wh
        by_priority[load["priority"]] = by_priority.get(load["priority"], 0) + wh
        breakdown.append({
            "id": load["id"],
            "name": load["name"],
            "watts": load["watts_draw"],
            "hours_per_day": load["hours_per_day"],
            "wh_per_day": round(wh, 2),
            "priority": load["priority"],
        })

    return {
        "total_wh_per_day": round(total_wh, 2),
        "by_priority": {k: round(v, 2) for k, v in by_priority.items()},
        "breakdown": breakdown,
    }


@router.get("/supply")
def calculate_supply() -> dict:
    # Solar production - average daily from last 7 days
    solar = query(
        """SELECT SUM(watts_output) / MAX(1, COUNT(DISTINCT date(timestamp))) as avg_daily_wh
           FROM solar_output
           WHERE timestamp >= datetime('now', '-7 days')"""
    )
    solar_wh = solar[0]["avg_daily_wh"] if solar and solar[0]["avg_daily_wh"] else 0

    # Battery capacity
    banks = query("SELECT SUM(capacity_ah * voltage) as total_wh FROM battery_banks")
    battery_wh = banks[0]["total_wh"] if banks and banks[0]["total_wh"] else 0

    # Generator capacity (assuming 8 hours run-time max per day)
    gens = query("SELECT SUM(rated_kw) as total_kw FROM generators")
    gen_kw = gens[0]["total_kw"] if gens and gens[0]["total_kw"] else 0
    gen_wh = gen_kw * 1000 * 8  # 8 hours max daily

    return {
        "solar_wh_per_day": round(solar_wh, 2),
        "battery_capacity_wh": round(battery_wh, 2),
        "generator_wh_per_day_max": round(gen_wh, 2),
        "total_available_wh": round(solar_wh + battery_wh + gen_wh, 2),
    }


@router.get("/analysis")
def budget_analysis() -> dict:
    demand = calculate_demand()
    supply = calculate_supply()

    total_demand = demand["total_wh_per_day"]
    total_supply = supply["total_available_wh"]
    surplus = total_supply - total_demand

    return {
        "demand": demand,
        "supply": supply,
        "surplus_wh": round(surplus, 2),
        "status": "surplus" if surplus >= 0 else "deficit",
    }


@router.get("/load-shedding")
def load_shedding_recommendations() -> dict:
    demand = calculate_demand()
    supply = calculate_supply()

    total_demand = demand["total_wh_per_day"]
    total_supply = supply["total_available_wh"]

    if total_supply >= total_demand:
        return {
            "needed": False,
            "message": "Supply meets demand. No load shedding needed.",
            "surplus_wh": round(total_supply - total_demand, 2),
            "cuts": [],
        }

    deficit = total_demand - total_supply
    cuts = []
    remaining_deficit = deficit

    # Cut optional loads first, then important
    for priority in ["optional", "important"]:
        loads = [l for l in demand["breakdown"] if l["priority"] == priority]
        loads.sort(key=lambda l: l["wh_per_day"], reverse=True)
        for load in loads:
            if remaining_deficit <= 0:
                break
            cuts.append({
                "id": load["id"],
                "name": load["name"],
                "priority": load["priority"],
                "wh_saved": load["wh_per_day"],
            })
            remaining_deficit -= load["wh_per_day"]

    return {
        "needed": True,
        "deficit_wh": round(deficit, 2),
        "cuts": cuts,
        "resolved": remaining_deficit <= 0,
        "remaining_deficit_wh": round(max(0, remaining_deficit), 2),
    }
