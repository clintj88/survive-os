"""Generator management API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/generators", tags=["generators"])


class GeneratorCreate(BaseModel):
    name: str
    fuel_type: str
    rated_kw: float
    location: str = ""
    install_date: Optional[str] = None
    total_runtime_hours: float = 0.0


class GeneratorUpdate(BaseModel):
    name: Optional[str] = None
    fuel_type: Optional[str] = None
    rated_kw: Optional[float] = None
    location: Optional[str] = None
    total_runtime_hours: Optional[float] = None


class RuntimeLog(BaseModel):
    generator_id: int
    start_time: str
    end_time: Optional[str] = None
    fuel_consumed: float = 0.0
    load_percent: float = 0.0


class MaintenanceScheduleCreate(BaseModel):
    generator_id: int
    task: str
    interval_hours: float
    last_performed_hours: float = 0.0
    last_performed_date: Optional[str] = None


class MaintenanceComplete(BaseModel):
    performed_by: str = ""
    notes: str = ""


@router.get("")
def list_generators() -> list[dict]:
    return query("SELECT * FROM generators ORDER BY name")


@router.post("", status_code=201)
def create_generator(gen: GeneratorCreate) -> dict:
    gen_id = execute(
        """INSERT INTO generators (name, fuel_type, rated_kw, location,
           install_date, total_runtime_hours) VALUES (?, ?, ?, ?, ?, ?)""",
        (gen.name, gen.fuel_type, gen.rated_kw, gen.location,
         gen.install_date, gen.total_runtime_hours),
    )
    results = query("SELECT * FROM generators WHERE id = ?", (gen_id,))
    return results[0]


@router.get("/maintenance-due")
def maintenance_due() -> list[dict]:
    gens = query("SELECT * FROM generators")
    due_items = []
    for g in gens:
        schedules = query(
            "SELECT * FROM generator_maintenance_schedule WHERE generator_id = ?",
            (g["id"],),
        )
        for s in schedules:
            hours_since = g["total_runtime_hours"] - s["last_performed_hours"]
            if hours_since >= s["interval_hours"]:
                due_items.append({
                    "generator_id": g["id"],
                    "generator_name": g["name"],
                    "schedule_id": s["id"],
                    "task": s["task"],
                    "interval_hours": s["interval_hours"],
                    "hours_since_last": round(hours_since, 1),
                    "hours_overdue": round(hours_since - s["interval_hours"], 1),
                })
    return due_items


@router.get("/{gen_id}")
def get_generator(gen_id: int) -> dict:
    results = query("SELECT * FROM generators WHERE id = ?", (gen_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Generator not found")
    return results[0]


@router.put("/{gen_id}")
def update_generator(gen_id: int, gen: GeneratorUpdate) -> dict:
    existing = query("SELECT id FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "fuel_type", "rated_kw", "location", "total_runtime_hours"]:
        value = getattr(gen, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(gen_id)
    execute(f"UPDATE generators SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_generator(gen_id)


@router.delete("/{gen_id}", status_code=204)
def delete_generator(gen_id: int) -> None:
    existing = query("SELECT id FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")
    execute("DELETE FROM generator_runtime WHERE generator_id = ?", (gen_id,))
    execute("DELETE FROM generator_maintenance_history WHERE generator_id = ?", (gen_id,))
    execute("DELETE FROM generator_maintenance_schedule WHERE generator_id = ?", (gen_id,))
    execute("DELETE FROM generators WHERE id = ?", (gen_id,))


@router.post("/runtime", status_code=201)
def log_runtime(entry: RuntimeLog) -> dict:
    existing = query("SELECT * FROM generators WHERE id = ?", (entry.generator_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")

    row_id = execute(
        """INSERT INTO generator_runtime (generator_id, start_time, end_time,
           fuel_consumed, load_percent) VALUES (?, ?, ?, ?, ?)""",
        (entry.generator_id, entry.start_time, entry.end_time,
         entry.fuel_consumed, entry.load_percent),
    )

    # Update total runtime hours if end_time provided
    if entry.end_time:
        hours = query(
            """SELECT (julianday(?) - julianday(?)) * 24 as hours""",
            (entry.end_time, entry.start_time),
        )
        if hours and hours[0]["hours"] and hours[0]["hours"] > 0:
            execute(
                "UPDATE generators SET total_runtime_hours = total_runtime_hours + ? WHERE id = ?",
                (hours[0]["hours"], entry.generator_id),
            )

    results = query("SELECT * FROM generator_runtime WHERE id = ?", (row_id,))
    return results[0]


@router.get("/runtime/{gen_id}")
def get_runtime_history(
    gen_id: int,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict]:
    existing = query("SELECT id FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")
    return query(
        "SELECT * FROM generator_runtime WHERE generator_id = ? ORDER BY start_time DESC LIMIT ?",
        (gen_id, limit),
    )


@router.get("/efficiency/{gen_id}")
def fuel_efficiency(gen_id: int) -> dict:
    existing = query("SELECT * FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")
    gen = existing[0]

    runs = query(
        """SELECT SUM(fuel_consumed) as total_fuel,
                  SUM((julianday(end_time) - julianday(start_time)) * 24) as total_hours,
                  AVG(load_percent) as avg_load
           FROM generator_runtime
           WHERE generator_id = ? AND end_time IS NOT NULL""",
        (gen_id,),
    )

    total_fuel = runs[0]["total_fuel"] if runs and runs[0]["total_fuel"] else 0
    total_hours = runs[0]["total_hours"] if runs and runs[0]["total_hours"] else 0
    avg_load = runs[0]["avg_load"] if runs and runs[0]["avg_load"] else 0

    kwh_generated = total_hours * gen["rated_kw"] * (avg_load / 100) if total_hours > 0 and avg_load > 0 else 0
    kwh_per_liter = kwh_generated / total_fuel if total_fuel > 0 else 0

    return {
        "generator_id": gen_id,
        "name": gen["name"],
        "total_fuel_consumed": round(total_fuel, 2),
        "total_runtime_hours": round(total_hours, 2),
        "avg_load_percent": round(avg_load, 1),
        "estimated_kwh_generated": round(kwh_generated, 2),
        "kwh_per_liter": round(kwh_per_liter, 2),
    }


# --- Maintenance ---

@router.get("/maintenance/{gen_id}")
def get_maintenance_schedule(gen_id: int) -> list[dict]:
    existing = query("SELECT id FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")
    gen = query("SELECT * FROM generators WHERE id = ?", (gen_id,))
    schedules = query(
        "SELECT * FROM generator_maintenance_schedule WHERE generator_id = ? ORDER BY task",
        (gen_id,),
    )
    total_hours = gen[0]["total_runtime_hours"]
    for s in schedules:
        hours_since = total_hours - s["last_performed_hours"]
        s["hours_since_last"] = round(hours_since, 1)
        s["due"] = hours_since >= s["interval_hours"]
    return schedules


@router.post("/maintenance", status_code=201)
def create_maintenance_schedule(entry: MaintenanceScheduleCreate) -> dict:
    existing = query("SELECT id FROM generators WHERE id = ?", (entry.generator_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")

    row_id = execute(
        """INSERT INTO generator_maintenance_schedule (generator_id, task,
           interval_hours, last_performed_hours, last_performed_date)
           VALUES (?, ?, ?, ?, ?)""",
        (entry.generator_id, entry.task, entry.interval_hours,
         entry.last_performed_hours, entry.last_performed_date),
    )
    results = query("SELECT * FROM generator_maintenance_schedule WHERE id = ?", (row_id,))
    return results[0]


@router.post("/maintenance/{schedule_id}/complete")
def complete_maintenance(schedule_id: int, body: MaintenanceComplete) -> dict:
    schedule = query("SELECT * FROM generator_maintenance_schedule WHERE id = ?", (schedule_id,))
    if not schedule:
        raise HTTPException(status_code=404, detail="Maintenance schedule not found")
    s = schedule[0]

    gen = query("SELECT total_runtime_hours FROM generators WHERE id = ?", (s["generator_id"],))
    current_hours = gen[0]["total_runtime_hours"]

    execute(
        """UPDATE generator_maintenance_schedule
           SET last_performed_hours = ?, last_performed_date = datetime('now')
           WHERE id = ?""",
        (current_hours, schedule_id),
    )

    execute(
        """INSERT INTO generator_maintenance_history
           (generator_id, task, performed_by, at_runtime_hours, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (s["generator_id"], s["task"], body.performed_by, current_hours, body.notes),
    )

    results = query("SELECT * FROM generator_maintenance_schedule WHERE id = ?", (schedule_id,))
    return results[0]


@router.get("/maintenance-history/{gen_id}")
def get_maintenance_history(
    gen_id: int,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict]:
    existing = query("SELECT id FROM generators WHERE id = ?", (gen_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Generator not found")
    return query(
        """SELECT * FROM generator_maintenance_history
           WHERE generator_id = ? ORDER BY performed_date DESC LIMIT ?""",
        (gen_id, limit),
    )
