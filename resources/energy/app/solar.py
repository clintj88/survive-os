"""Solar panel monitoring API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/solar", tags=["solar"])


class PanelCreate(BaseModel):
    name: str
    rated_watts: float
    location: str = ""
    install_date: Optional[str] = None
    orientation: str = "south"
    tilt_angle: float = 30.0


class PanelUpdate(BaseModel):
    name: Optional[str] = None
    rated_watts: Optional[float] = None
    location: Optional[str] = None
    orientation: Optional[str] = None
    tilt_angle: Optional[float] = None


class OutputLog(BaseModel):
    panel_id: int
    watts_output: float
    irradiance: Optional[float] = None
    timestamp: Optional[str] = None


@router.get("/panels")
def list_panels() -> list[dict]:
    return query("SELECT * FROM solar_panels ORDER BY name")


@router.post("/panels", status_code=201)
def create_panel(panel: PanelCreate) -> dict:
    panel_id = execute(
        """INSERT INTO solar_panels (name, rated_watts, location, install_date,
           orientation, tilt_angle) VALUES (?, ?, ?, ?, ?, ?)""",
        (panel.name, panel.rated_watts, panel.location, panel.install_date,
         panel.orientation, panel.tilt_angle),
    )
    results = query("SELECT * FROM solar_panels WHERE id = ?", (panel_id,))
    return results[0]


@router.get("/panels/{panel_id}")
def get_panel(panel_id: int) -> dict:
    results = query("SELECT * FROM solar_panels WHERE id = ?", (panel_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Panel not found")
    return results[0]


@router.put("/panels/{panel_id}")
def update_panel(panel_id: int, panel: PanelUpdate) -> dict:
    existing = query("SELECT id FROM solar_panels WHERE id = ?", (panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "rated_watts", "location", "orientation", "tilt_angle"]:
        value = getattr(panel, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(panel_id)
    execute(f"UPDATE solar_panels SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_panel(panel_id)


@router.delete("/panels/{panel_id}", status_code=204)
def delete_panel(panel_id: int) -> None:
    existing = query("SELECT id FROM solar_panels WHERE id = ?", (panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")
    execute("DELETE FROM solar_output WHERE panel_id = ?", (panel_id,))
    execute("DELETE FROM solar_panels WHERE id = ?", (panel_id,))


@router.post("/output", status_code=201)
def log_output(entry: OutputLog) -> dict:
    existing = query("SELECT id FROM solar_panels WHERE id = ?", (entry.panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")

    if entry.timestamp:
        row_id = execute(
            """INSERT INTO solar_output (panel_id, timestamp, watts_output, irradiance)
               VALUES (?, ?, ?, ?)""",
            (entry.panel_id, entry.timestamp, entry.watts_output, entry.irradiance),
        )
    else:
        row_id = execute(
            """INSERT INTO solar_output (panel_id, watts_output, irradiance)
               VALUES (?, ?, ?)""",
            (entry.panel_id, entry.watts_output, entry.irradiance),
        )
    results = query("SELECT * FROM solar_output WHERE id = ?", (row_id,))
    return results[0]


@router.get("/output/{panel_id}")
def get_output(
    panel_id: int,
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    existing = query("SELECT id FROM solar_panels WHERE id = ?", (panel_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Panel not found")
    return query(
        "SELECT * FROM solar_output WHERE panel_id = ? ORDER BY timestamp DESC LIMIT ?",
        (panel_id, limit),
    )


@router.get("/production/daily")
def daily_production(
    panel_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
) -> list[dict]:
    if panel_id:
        return query(
            """SELECT panel_id, date(timestamp) as date,
                      SUM(watts_output) as total_wh, COUNT(*) as readings
               FROM solar_output WHERE panel_id = ?
               GROUP BY panel_id, date(timestamp)
               ORDER BY date DESC LIMIT ?""",
            (panel_id, days),
        )
    return query(
        """SELECT panel_id, date(timestamp) as date,
                  SUM(watts_output) as total_wh, COUNT(*) as readings
           FROM solar_output
           GROUP BY panel_id, date(timestamp)
           ORDER BY date DESC LIMIT ?""",
        (days,),
    )


@router.get("/efficiency")
def panel_efficiency() -> list[dict]:
    panels = query("SELECT * FROM solar_panels")
    result = []
    for p in panels:
        avg_output = query(
            "SELECT AVG(watts_output) as avg_watts FROM solar_output WHERE panel_id = ?",
            (p["id"],),
        )
        avg_watts = avg_output[0]["avg_watts"] if avg_output and avg_output[0]["avg_watts"] else 0
        efficiency = (avg_watts / p["rated_watts"] * 100) if p["rated_watts"] > 0 else 0
        result.append({
            "panel_id": p["id"],
            "name": p["name"],
            "rated_watts": p["rated_watts"],
            "avg_output_watts": round(avg_watts, 2),
            "efficiency_percent": round(efficiency, 2),
        })
    return result
