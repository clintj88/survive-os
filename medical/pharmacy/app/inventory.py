"""Pharmacy inventory management routes."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class MedicationCreate(BaseModel):
    name: str
    generic_name: str = ""
    category: str = ""
    form: str = "tablet"
    strength: str = ""
    unit: str = ""
    notes: str = ""


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    category: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class LotCreate(BaseModel):
    medication_id: int
    lot_number: str = ""
    quantity: int
    expiration_date: str
    supplier: str = ""
    date_received: str = ""
    storage_location: str = ""


class DispenseRequest(BaseModel):
    medication_id: int
    quantity: int
    prescription_id: int
    dispensed_by: str


# --- Medication CRUD ---

@router.get("/medications")
def list_medications(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    conditions: list[str] = []
    params: list[str] = []
    if search:
        conditions.append("(m.name LIKE ? OR m.generic_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if category:
        conditions.append("m.category = ?")
        params.append(category)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT m.*, COALESCE(SUM(l.quantity), 0) as total_stock
            FROM medications m
            LEFT JOIN inventory_lots l ON l.medication_id = m.id
                AND l.quantity > 0
                AND l.expiration_date > datetime('now')
            {where}
            GROUP BY m.id
            ORDER BY m.name""",
        tuple(params),
    )


@router.get("/medications/{med_id}")
def get_medication(
    med_id: int,
    _role: str = Depends(require_medical_role),
) -> dict:
    results = query("SELECT * FROM medications WHERE id = ?", (med_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Medication not found")
    med = results[0]
    med["lots"] = query(
        """SELECT * FROM inventory_lots
           WHERE medication_id = ? AND quantity > 0
           ORDER BY expiration_date""",
        (med_id,),
    )
    return med


@router.post("/medications", status_code=201)
def create_medication(
    med: MedicationCreate,
    _role: str = Depends(require_medical_role),
) -> dict:
    med_id = execute(
        """INSERT INTO medications (name, generic_name, category, form, strength, unit, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (med.name, med.generic_name, med.category, med.form, med.strength, med.unit, med.notes),
    )
    return query("SELECT * FROM medications WHERE id = ?", (med_id,))[0]


@router.put("/medications/{med_id}")
def update_medication(
    med_id: int,
    med: MedicationUpdate,
    _role: str = Depends(require_medical_role),
) -> dict:
    existing = query("SELECT id FROM medications WHERE id = ?", (med_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Medication not found")
    updates: list[str] = []
    params: list = []
    for field in ["name", "generic_name", "category", "form", "strength", "unit", "notes"]:
        value = getattr(med, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(med_id)
    execute(f"UPDATE medications SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return query("SELECT * FROM medications WHERE id = ?", (med_id,))[0]


@router.delete("/medications/{med_id}", status_code=204)
def delete_medication(
    med_id: int,
    _role: str = Depends(require_medical_role),
) -> None:
    existing = query("SELECT id FROM medications WHERE id = ?", (med_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Medication not found")
    execute("DELETE FROM inventory_lots WHERE medication_id = ?", (med_id,))
    execute("DELETE FROM medications WHERE id = ?", (med_id,))


# --- Inventory Lots ---

@router.post("/lots", status_code=201)
def create_lot(
    lot: LotCreate,
    _role: str = Depends(require_medical_role),
) -> dict:
    meds = query("SELECT id FROM medications WHERE id = ?", (lot.medication_id,))
    if not meds:
        raise HTTPException(status_code=400, detail="Medication not found")
    date_received = lot.date_received or datetime.now(timezone.utc).isoformat()
    lot_id = execute(
        """INSERT INTO inventory_lots
           (medication_id, lot_number, quantity, expiration_date, supplier, date_received, storage_location)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (lot.medication_id, lot.lot_number, lot.quantity, lot.expiration_date,
         lot.supplier, date_received, lot.storage_location),
    )
    return query("SELECT * FROM inventory_lots WHERE id = ?", (lot_id,))[0]


@router.get("/lots")
def list_lots(
    medication_id: Optional[int] = Query(None),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    if medication_id:
        return query(
            """SELECT l.*, m.name as medication_name
               FROM inventory_lots l JOIN medications m ON l.medication_id = m.id
               WHERE l.medication_id = ? ORDER BY l.expiration_date""",
            (medication_id,),
        )
    return query(
        """SELECT l.*, m.name as medication_name
           FROM inventory_lots l JOIN medications m ON l.medication_id = m.id
           ORDER BY l.expiration_date""",
    )


# --- Dispensing ---

@router.post("/dispense")
def dispense_medication(
    req: DispenseRequest,
    _role: str = Depends(require_medical_role),
) -> dict:
    """Dispense medication using FIFO by expiration date."""
    # Verify prescription exists and is active
    rx = query(
        "SELECT * FROM prescriptions WHERE id = ? AND status = 'active'",
        (req.prescription_id,),
    )
    if not rx:
        raise HTTPException(status_code=400, detail="Active prescription not found")

    # Get available lots (FIFO by expiration, exclude expired)
    lots = query(
        """SELECT * FROM inventory_lots
           WHERE medication_id = ? AND quantity > 0 AND expiration_date > datetime('now')
           ORDER BY expiration_date ASC""",
        (req.medication_id,),
    )

    remaining = req.quantity
    dispensed_lots: list[dict] = []

    for lot in lots:
        if remaining <= 0:
            break
        take = min(remaining, lot["quantity"])
        execute(
            "UPDATE inventory_lots SET quantity = quantity - ? WHERE id = ?",
            (take, lot["id"]),
        )
        execute(
            """INSERT INTO dispensing_log (prescription_id, lot_id, quantity, dispensed_by)
               VALUES (?, ?, ?, ?)""",
            (req.prescription_id, lot["id"], take, req.dispensed_by),
        )
        dispensed_lots.append({"lot_id": lot["id"], "quantity": take})
        remaining -= take

    if remaining > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Short by {remaining} units.",
        )

    return {"dispensed": dispensed_lots, "total_dispensed": req.quantity}


# --- Expiration Alerts ---

@router.get("/expiring")
def get_expiring_medications(
    days: int = Query(default=90, ge=1),
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    """Get medications expiring within the specified number of days."""
    return query(
        """SELECT l.*, m.name as medication_name, m.generic_name, m.form, m.strength,
                  CAST(julianday(l.expiration_date) - julianday('now') AS INTEGER) as days_until_expiry
           FROM inventory_lots l
           JOIN medications m ON l.medication_id = m.id
           WHERE l.quantity > 0
             AND l.expiration_date > datetime('now')
             AND l.expiration_date <= datetime('now', '+' || ? || ' days')
           ORDER BY l.expiration_date ASC""",
        (days,),
    )


@router.get("/expired")
def get_expired_medications(
    _role: str = Depends(require_medical_role),
) -> list[dict]:
    """Get all expired medication lots with remaining quantity."""
    return query(
        """SELECT l.*, m.name as medication_name, m.generic_name
           FROM inventory_lots l
           JOIN medications m ON l.medication_id = m.id
           WHERE l.quantity > 0 AND l.expiration_date <= datetime('now')
           ORDER BY l.expiration_date ASC""",
    )
