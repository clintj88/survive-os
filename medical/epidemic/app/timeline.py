"""Historical epidemic timeline routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


class EpidemicEventCreate(BaseModel):
    name: str
    pathogen: str = "unknown"
    start_date: str
    end_date: Optional[str] = None
    total_cases: int = 0
    total_deaths: int = 0
    response_actions: str = ""
    lessons_learned: str = ""


class EpidemicEventUpdate(BaseModel):
    name: Optional[str] = None
    pathogen: Optional[str] = None
    end_date: Optional[str] = None
    total_cases: Optional[int] = None
    total_deaths: Optional[int] = None
    response_actions: Optional[str] = None
    lessons_learned: Optional[str] = None


@router.get("/events")
def list_events(_: str = Depends(require_medical_role)) -> list[dict]:
    return query("SELECT * FROM epidemic_events ORDER BY start_date DESC")


@router.get("/events/{event_id}")
def get_event(event_id: int, _: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM epidemic_events WHERE id = ?", (event_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Event not found")
    return results[0]


@router.post("/events", status_code=201)
def create_event(
    event: EpidemicEventCreate, _: str = Depends(require_medical_role)
) -> dict:
    eid = execute(
        """INSERT INTO epidemic_events
           (name, pathogen, start_date, end_date, total_cases, total_deaths,
            response_actions, lessons_learned)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event.name, event.pathogen, event.start_date, event.end_date,
            event.total_cases, event.total_deaths, event.response_actions,
            event.lessons_learned,
        ),
    )
    return get_event(eid)


@router.put("/events/{event_id}")
def update_event(
    event_id: int, event: EpidemicEventUpdate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM epidemic_events WHERE id = ?", (event_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    updates: list[str] = []
    params: list = []
    for field in (
        "name", "pathogen", "end_date", "total_cases",
        "total_deaths", "response_actions", "lessons_learned",
    ):
        value = getattr(event, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(event_id)
    execute(f"UPDATE epidemic_events SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_event(event_id)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, _: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM epidemic_events WHERE id = ?", (event_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    execute("DELETE FROM epidemic_events WHERE id = ?", (event_id,))


@router.get("/compare")
def compare_with_history(
    syndrome: str = Query(...),
    _: str = Depends(require_medical_role),
) -> dict:
    """Compare current syndromic data against historical outbreaks."""
    # Get current syndrome counts
    current = query(
        """SELECT date, COUNT(*) as count FROM symptom_reports
           WHERE syndrome = ?
           GROUP BY date ORDER BY date""",
        (syndrome,),
    )

    # Get historical events with matching pathogen/name patterns
    historical = query(
        """SELECT * FROM epidemic_events
           WHERE name LIKE ? OR pathogen LIKE ?
           ORDER BY start_date""",
        (f"%{syndrome}%", f"%{syndrome}%"),
    )

    return {
        "syndrome": syndrome,
        "current_trend": current,
        "historical_matches": historical,
    }
