"""Seed lot inventory CRUD and ledger tracking."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class SeedLotCreate(BaseModel):
    name: str
    species: str
    variety: str = ""
    quantity: float = 0
    unit: str = "grams"
    source: str = ""
    date_collected: str = ""
    storage_location: str = ""
    storage_temp: Optional[float] = None
    storage_humidity: Optional[float] = None
    low_stock_threshold: float = 50
    notes: str = ""


class SeedLotUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    variety: Optional[str] = None
    source: Optional[str] = None
    storage_location: Optional[str] = None
    storage_temp: Optional[float] = None
    storage_humidity: Optional[float] = None
    low_stock_threshold: Optional[float] = None
    notes: Optional[str] = None


class LedgerEntry(BaseModel):
    type: str  # deposit or withdrawal
    amount: float
    reason: str = ""
    performed_by: str = "system"


@router.get("/lots")
def list_lots(
    species: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> list[dict]:
    conditions = []
    params: list = []
    if species:
        conditions.append("species = ?")
        params.append(species)
    if search:
        conditions.append("(name LIKE ? OR variety LIKE ? OR notes LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"SELECT * FROM seed_lots {where} ORDER BY species, name",
        tuple(params),
    )


@router.get("/lots/{lot_id}")
def get_lot(lot_id: int) -> dict:
    results = query("SELECT * FROM seed_lots WHERE id = ?", (lot_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    return results[0]


@router.post("/lots", status_code=201)
def create_lot(lot: SeedLotCreate) -> dict:
    date_collected = lot.date_collected or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lot_id = execute(
        """INSERT INTO seed_lots
           (name, species, variety, quantity, unit, source, date_collected,
            storage_location, storage_temp, storage_humidity, low_stock_threshold, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            lot.name, lot.species, lot.variety, lot.quantity, lot.unit,
            lot.source, date_collected, lot.storage_location,
            lot.storage_temp, lot.storage_humidity,
            lot.low_stock_threshold, lot.notes,
        ),
    )
    if lot.quantity > 0:
        execute(
            "INSERT INTO ledger (lot_id, type, amount, reason) VALUES (?, 'deposit', ?, 'Initial stock')",
            (lot_id, lot.quantity),
        )
    return get_lot(lot_id)


@router.put("/lots/{lot_id}")
def update_lot(lot_id: int, lot: SeedLotUpdate) -> dict:
    existing = query("SELECT id FROM seed_lots WHERE id = ?", (lot_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Seed lot not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "species", "variety", "source", "storage_location",
                  "storage_temp", "storage_humidity", "low_stock_threshold", "notes"]:
        value = getattr(lot, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(lot_id)
    execute(f"UPDATE seed_lots SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_lot(lot_id)


@router.delete("/lots/{lot_id}", status_code=204)
def delete_lot(lot_id: int) -> None:
    existing = query("SELECT id FROM seed_lots WHERE id = ?", (lot_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    execute("DELETE FROM ledger WHERE lot_id = ?", (lot_id,))
    execute("DELETE FROM germination_tests WHERE lot_id = ?", (lot_id,))
    execute("DELETE FROM seed_lots WHERE id = ?", (lot_id,))


@router.post("/lots/{lot_id}/ledger", status_code=201)
def add_ledger_entry(lot_id: int, entry: LedgerEntry) -> dict:
    lot = query("SELECT id, quantity FROM seed_lots WHERE id = ?", (lot_id,))
    if not lot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    if entry.type not in ("deposit", "withdrawal"):
        raise HTTPException(status_code=400, detail="Type must be 'deposit' or 'withdrawal'")
    if entry.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    current_qty = lot[0]["quantity"]
    if entry.type == "withdrawal" and entry.amount > current_qty:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    new_qty = current_qty + entry.amount if entry.type == "deposit" else current_qty - entry.amount
    execute("UPDATE seed_lots SET quantity = ?, updated_at = ? WHERE id = ?",
            (new_qty, datetime.now(timezone.utc).isoformat(), lot_id))

    entry_id = execute(
        "INSERT INTO ledger (lot_id, type, amount, reason, performed_by) VALUES (?, ?, ?, ?, ?)",
        (lot_id, entry.type, entry.amount, entry.reason, entry.performed_by),
    )
    results = query("SELECT * FROM ledger WHERE id = ?", (entry_id,))
    return results[0]


@router.get("/lots/{lot_id}/ledger")
def get_ledger(lot_id: int) -> list[dict]:
    lot = query("SELECT id FROM seed_lots WHERE id = ?", (lot_id,))
    if not lot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    return query("SELECT * FROM ledger WHERE lot_id = ? ORDER BY created_at DESC", (lot_id,))


@router.get("/alerts/low-stock")
def low_stock_alerts() -> list[dict]:
    return query(
        "SELECT * FROM seed_lots WHERE quantity <= low_stock_threshold ORDER BY quantity ASC"
    )


@router.get("/species")
def list_species() -> list[dict]:
    return query("SELECT DISTINCT species FROM seed_lots ORDER BY species")
