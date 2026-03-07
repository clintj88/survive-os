"""Contact scheduler API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    title: str
    callsign: str = ""
    freq_mhz: Optional[float] = None
    mode: str = ""
    scheduled_at: str
    duration_minutes: int = 30
    notes: str = ""
    recurring: str = "none"


class ContactUpdate(BaseModel):
    title: Optional[str] = None
    callsign: Optional[str] = None
    freq_mhz: Optional[float] = None
    mode: Optional[str] = None
    scheduled_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    recurring: Optional[str] = None


@router.get("")
def list_contacts(upcoming: Optional[bool] = Query(None)) -> list[dict]:
    if upcoming:
        return query(
            "SELECT * FROM scheduled_contacts WHERE scheduled_at >= datetime('now') ORDER BY scheduled_at"
        )
    return query("SELECT * FROM scheduled_contacts ORDER BY scheduled_at DESC")


@router.get("/{contact_id}")
def get_contact(contact_id: int) -> dict:
    results = query("SELECT * FROM scheduled_contacts WHERE id = ?", (contact_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Contact not found")
    return results[0]


@router.post("", status_code=201)
def create_contact(contact: ContactCreate) -> dict:
    cid = execute(
        """INSERT INTO scheduled_contacts
           (title, callsign, freq_mhz, mode, scheduled_at, duration_minutes, notes, recurring)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            contact.title, contact.callsign, contact.freq_mhz, contact.mode,
            contact.scheduled_at, contact.duration_minutes, contact.notes, contact.recurring,
        ),
    )
    return get_contact(cid)


@router.put("/{contact_id}")
def update_contact(contact_id: int, contact: ContactUpdate) -> dict:
    existing = query("SELECT id FROM scheduled_contacts WHERE id = ?", (contact_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")

    updates: list[str] = []
    params: list = []
    for field in ["title", "callsign", "freq_mhz", "mode", "scheduled_at",
                  "duration_minutes", "notes", "recurring"]:
        val = getattr(contact, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(contact_id)
    execute(f"UPDATE scheduled_contacts SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_contact(contact_id)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int) -> None:
    existing = query("SELECT id FROM scheduled_contacts WHERE id = ?", (contact_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    execute("DELETE FROM scheduled_contacts WHERE id = ?", (contact_id,))
