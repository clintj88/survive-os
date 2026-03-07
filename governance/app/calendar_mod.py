"""Community Calendar routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class EventCreate(BaseModel):
    title: str
    event_date: str
    event_time: str = ""
    location: str = ""
    event_type: str = "meeting"
    description: str = ""
    recurring: bool = False


@router.get("/events")
def list_events(
    event_type: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM calendar_events WHERE 1=1"
    params: list = []
    if event_type:
        sql += " AND event_type = ?"
        params.append(event_type)
    if month:
        sql += " AND event_date LIKE ?"
        params.append(f"{month}%")
    sql += " ORDER BY event_date, event_time"
    return query(sql, tuple(params))


@router.get("/events/{event_id}")
def get_event(event_id: int) -> dict:
    results = query("SELECT * FROM calendar_events WHERE id = ?", (event_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Event not found")
    return results[0]


@router.post("/events", status_code=201)
def create_event(event: EventCreate) -> dict:
    eid = execute(
        """INSERT INTO calendar_events (title, event_date, event_time, location, event_type, description, recurring)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (event.title, event.event_date, event.event_time, event.location,
         event.event_type, event.description, 1 if event.recurring else 0),
    )
    return get_event(eid)


@router.get("/upcoming")
def upcoming_events(days: int = Query(default=30)) -> list[dict]:
    return query(
        "SELECT * FROM calendar_events WHERE event_date >= date('now') AND event_date <= date('now', ? || ' days') ORDER BY event_date, event_time",
        (str(days),),
    )
