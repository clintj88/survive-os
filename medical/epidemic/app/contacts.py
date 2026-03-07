"""Contact tracing routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    case_id: int
    contact_person: str
    relationship: str = ""
    date_of_contact: str
    exposure_type: str = "casual"
    notes: str = ""


class ContactUpdate(BaseModel):
    follow_up_status: Optional[str] = None
    risk_score: Optional[float] = None
    notes: Optional[str] = None
    exposure_type: Optional[str] = None


EXPOSURE_RISK = {"close": 0.8, "casual": 0.3}


@router.get("")
def list_contacts(
    case_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if case_id is not None:
        conditions.append("c.case_id = ?")
        params.append(case_id)
    if status:
        conditions.append("c.follow_up_status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT c.*, sr.syndrome, sr.date as case_date
            FROM contacts c
            LEFT JOIN symptom_reports sr ON c.case_id = sr.id
            {where}
            ORDER BY c.date_of_contact DESC""",
        tuple(params),
    )


@router.get("/{contact_id}")
def get_contact(contact_id: int, _: str = Depends(require_medical_role)) -> dict:
    results = query(
        """SELECT c.*, sr.syndrome, sr.date as case_date
           FROM contacts c
           LEFT JOIN symptom_reports sr ON c.case_id = sr.id
           WHERE c.id = ?""",
        (contact_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Contact not found")
    return results[0]


@router.post("", status_code=201)
def create_contact(
    contact: ContactCreate, _: str = Depends(require_medical_role)
) -> dict:
    # Verify case exists
    cases = query("SELECT id FROM symptom_reports WHERE id = ?", (contact.case_id,))
    if not cases:
        raise HTTPException(status_code=400, detail="Case not found")

    if contact.exposure_type not in ("close", "casual"):
        raise HTTPException(status_code=400, detail="Exposure type must be 'close' or 'casual'")

    risk_score = EXPOSURE_RISK.get(contact.exposure_type, 0.3)

    contact_id = execute(
        """INSERT INTO contacts (case_id, contact_person, relationship, date_of_contact,
                                 exposure_type, risk_score, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (contact.case_id, contact.contact_person, contact.relationship,
         contact.date_of_contact, contact.exposure_type, risk_score, contact.notes),
    )
    return get_contact(contact_id)


@router.put("/{contact_id}")
def update_contact(
    contact_id: int, contact: ContactUpdate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM contacts WHERE id = ?", (contact_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")

    updates: list[str] = []
    params: list = []
    for field in ("follow_up_status", "risk_score", "notes", "exposure_type"):
        value = getattr(contact, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(contact_id)
    execute(f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_contact(contact_id)


@router.get("/network/{case_id}")
def get_contact_network(case_id: int, _: str = Depends(require_medical_role)) -> dict:
    """Get contact network for a case (who exposed whom)."""
    # Get the primary case
    case = query("SELECT * FROM symptom_reports WHERE id = ?", (case_id,))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get direct contacts
    direct_contacts = query(
        """SELECT c.*, sr.syndrome, sr.date as case_date
           FROM contacts c
           LEFT JOIN symptom_reports sr ON c.case_id = sr.id
           WHERE c.case_id = ?""",
        (case_id,),
    )

    # Check if any contacts are themselves cases with their own contacts
    secondary: list[dict] = []
    for c in direct_contacts:
        # Find cases where the contact person is a patient
        linked = query(
            """SELECT sr.id as linked_case_id, sr.syndrome, sr.date
               FROM symptom_reports sr
               WHERE sr.patient_id = ?""",
            (c["contact_person"],),
        )
        if linked:
            for lk in linked:
                sub_contacts = query(
                    "SELECT * FROM contacts WHERE case_id = ?",
                    (lk["linked_case_id"],),
                )
                secondary.append({
                    "linked_case": lk,
                    "contacts": sub_contacts,
                })

    return {
        "case": case[0],
        "direct_contacts": direct_contacts,
        "secondary_links": secondary,
    }
