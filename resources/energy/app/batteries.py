"""Battery bank tracking API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/batteries", tags=["batteries"])


class BankCreate(BaseModel):
    name: str
    type: str
    capacity_ah: float
    voltage: float
    num_cells: int = 1
    install_date: Optional[str] = None


class BankUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    capacity_ah: Optional[float] = None
    voltage: Optional[float] = None
    num_cells: Optional[int] = None


class StateLog(BaseModel):
    bank_id: int
    voltage: float
    current_amps: float = 0.0
    soc_percent: float
    temperature: Optional[float] = None
    timestamp: Optional[str] = None


@router.get("/banks")
def list_banks() -> list[dict]:
    return query("SELECT * FROM battery_banks ORDER BY name")


@router.post("/banks", status_code=201)
def create_bank(bank: BankCreate) -> dict:
    bank_id = execute(
        """INSERT INTO battery_banks (name, type, capacity_ah, voltage, num_cells,
           install_date) VALUES (?, ?, ?, ?, ?, ?)""",
        (bank.name, bank.type, bank.capacity_ah, bank.voltage,
         bank.num_cells, bank.install_date),
    )
    results = query("SELECT * FROM battery_banks WHERE id = ?", (bank_id,))
    return results[0]


@router.get("/banks/{bank_id}")
def get_bank(bank_id: int) -> dict:
    results = query("SELECT * FROM battery_banks WHERE id = ?", (bank_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Battery bank not found")
    return results[0]


@router.put("/banks/{bank_id}")
def update_bank(bank_id: int, bank: BankUpdate) -> dict:
    existing = query("SELECT id FROM battery_banks WHERE id = ?", (bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")

    updates: list[str] = []
    params: list = []
    for field in ["name", "type", "capacity_ah", "voltage", "num_cells"]:
        value = getattr(bank, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(bank_id)
    execute(f"UPDATE battery_banks SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_bank(bank_id)


@router.delete("/banks/{bank_id}", status_code=204)
def delete_bank(bank_id: int) -> None:
    existing = query("SELECT id FROM battery_banks WHERE id = ?", (bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")
    execute("DELETE FROM battery_state WHERE bank_id = ?", (bank_id,))
    execute("DELETE FROM battery_banks WHERE id = ?", (bank_id,))


@router.post("/state", status_code=201)
def log_state(entry: StateLog) -> dict:
    existing = query("SELECT id FROM battery_banks WHERE id = ?", (entry.bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")

    if entry.timestamp:
        row_id = execute(
            """INSERT INTO battery_state (bank_id, timestamp, voltage, current_amps,
               soc_percent, temperature) VALUES (?, ?, ?, ?, ?, ?)""",
            (entry.bank_id, entry.timestamp, entry.voltage, entry.current_amps,
             entry.soc_percent, entry.temperature),
        )
    else:
        row_id = execute(
            """INSERT INTO battery_state (bank_id, voltage, current_amps,
               soc_percent, temperature) VALUES (?, ?, ?, ?, ?)""",
            (entry.bank_id, entry.voltage, entry.current_amps,
             entry.soc_percent, entry.temperature),
        )
    results = query("SELECT * FROM battery_state WHERE id = ?", (row_id,))
    return results[0]


@router.get("/state/{bank_id}")
def get_state_history(
    bank_id: int,
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    existing = query("SELECT id FROM battery_banks WHERE id = ?", (bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")
    return query(
        "SELECT * FROM battery_state WHERE bank_id = ? ORDER BY timestamp DESC LIMIT ?",
        (bank_id, limit),
    )


@router.get("/state/{bank_id}/latest")
def get_latest_state(bank_id: int) -> dict:
    existing = query("SELECT * FROM battery_banks WHERE id = ?", (bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")
    states = query(
        "SELECT * FROM battery_state WHERE bank_id = ? ORDER BY id DESC LIMIT 1",
        (bank_id,),
    )
    bank = existing[0]
    latest = states[0] if states else None
    return {
        "bank": bank,
        "latest_state": latest,
        "capacity_wh": bank["capacity_ah"] * bank["voltage"],
    }


@router.get("/cycles/{bank_id}")
def get_cycles(bank_id: int) -> dict:
    existing = query("SELECT * FROM battery_banks WHERE id = ?", (bank_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Battery bank not found")
    bank = existing[0]

    states = query(
        "SELECT soc_percent FROM battery_state WHERE bank_id = ? ORDER BY timestamp",
        (bank_id,),
    )

    cycles = 0
    prev_soc: Optional[float] = None
    charging = False
    for s in states:
        soc = s["soc_percent"]
        if prev_soc is not None:
            if soc > prev_soc and not charging:
                charging = True
            elif soc < prev_soc and charging:
                charging = False
                cycles += 1
        prev_soc = soc

    max_cycles = {"lead-acid": 500, "lithium": 2000, "nickel": 1000}
    expected = max_cycles.get(bank["type"], 1000)
    health_pct = max(0, round((1 - cycles / expected) * 100, 1)) if expected > 0 else 100

    return {
        "bank_id": bank_id,
        "name": bank["name"],
        "type": bank["type"],
        "estimated_cycles": cycles,
        "expected_max_cycles": expected,
        "health_percent": health_pct,
    }


@router.get("/low-battery")
def low_battery_alerts(
    threshold: float = Query(20.0, ge=0, le=100),
) -> list[dict]:
    return query(
        """SELECT b.id as bank_id, b.name, b.type, s.soc_percent, s.voltage,
                  s.temperature, s.timestamp
           FROM battery_banks b
           JOIN battery_state s ON s.bank_id = b.id
           WHERE s.id = (
               SELECT id FROM battery_state WHERE bank_id = b.id
               ORDER BY timestamp DESC LIMIT 1
           ) AND s.soc_percent <= ?
           ORDER BY s.soc_percent""",
        (threshold,),
    )
