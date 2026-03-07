"""Frequency database API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/frequencies", tags=["frequencies"])


class FrequencyCreate(BaseModel):
    freq_mhz: float
    name: str
    band: str
    mode: str
    usage: str = "general"
    notes: str = ""


class FrequencyUpdate(BaseModel):
    freq_mhz: Optional[float] = None
    name: Optional[str] = None
    band: Optional[str] = None
    mode: Optional[str] = None
    usage: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_frequencies(
    band: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    usage: Optional[str] = Query(None),
) -> list[dict]:
    sql = "SELECT * FROM frequencies WHERE 1=1"
    params: list = []
    if band:
        sql += " AND band = ?"
        params.append(band)
    if mode:
        sql += " AND mode = ?"
        params.append(mode)
    if usage:
        sql += " AND usage = ?"
        params.append(usage)
    sql += " ORDER BY freq_mhz"
    return query(sql, tuple(params))


@router.get("/{freq_id}")
def get_frequency(freq_id: int) -> dict:
    results = query("SELECT * FROM frequencies WHERE id = ?", (freq_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Frequency not found")
    return results[0]


@router.post("", status_code=201)
def create_frequency(freq: FrequencyCreate) -> dict:
    fid = execute(
        "INSERT INTO frequencies (freq_mhz, name, band, mode, usage, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (freq.freq_mhz, freq.name, freq.band, freq.mode, freq.usage, freq.notes),
    )
    return get_frequency(fid)


@router.put("/{freq_id}")
def update_frequency(freq_id: int, freq: FrequencyUpdate) -> dict:
    existing = query("SELECT id FROM frequencies WHERE id = ?", (freq_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Frequency not found")

    updates: list[str] = []
    params: list = []
    for field in ["freq_mhz", "name", "band", "mode", "usage", "notes"]:
        val = getattr(freq, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(freq_id)
    execute(f"UPDATE frequencies SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_frequency(freq_id)


@router.delete("/{freq_id}", status_code=204)
def delete_frequency(freq_id: int) -> None:
    existing = query("SELECT id FROM frequencies WHERE id = ?", (freq_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Frequency not found")
    execute("DELETE FROM frequencies WHERE id = ?", (freq_id,))
