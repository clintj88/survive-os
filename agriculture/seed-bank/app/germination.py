"""Germination rate tracking and test management."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/germination", tags=["germination"])


class GerminationTestCreate(BaseModel):
    lot_id: int
    date_tested: str = ""
    sample_size: int
    germination_count: int
    notes: str = ""


@router.post("/tests", status_code=201)
def create_test(test: GerminationTestCreate) -> dict:
    lot = query("SELECT id FROM seed_lots WHERE id = ?", (test.lot_id,))
    if not lot:
        raise HTTPException(status_code=404, detail="Seed lot not found")
    if test.germination_count > test.sample_size:
        raise HTTPException(status_code=400, detail="Germination count cannot exceed sample size")
    if test.sample_size <= 0:
        raise HTTPException(status_code=400, detail="Sample size must be positive")

    params = [test.lot_id, test.sample_size, test.germination_count, test.notes]
    if test.date_tested:
        test_id = execute(
            """INSERT INTO germination_tests (lot_id, date_tested, sample_size, germination_count, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (test.lot_id, test.date_tested, test.sample_size, test.germination_count, test.notes),
        )
    else:
        test_id = execute(
            """INSERT INTO germination_tests (lot_id, sample_size, germination_count, notes)
               VALUES (?, ?, ?, ?)""",
            (test.lot_id, test.sample_size, test.germination_count, test.notes),
        )

    results = query("SELECT * FROM germination_tests WHERE id = ?", (test_id,))
    result = results[0]
    result["germination_rate"] = round(test.germination_count / test.sample_size * 100, 1)
    return result


@router.get("/tests")
def list_tests(lot_id: Optional[int] = None) -> list[dict]:
    if lot_id:
        rows = query(
            """SELECT gt.*, sl.name as lot_name, sl.species, sl.variety
               FROM germination_tests gt
               JOIN seed_lots sl ON gt.lot_id = sl.id
               WHERE gt.lot_id = ?
               ORDER BY gt.date_tested DESC""",
            (lot_id,),
        )
    else:
        rows = query(
            """SELECT gt.*, sl.name as lot_name, sl.species, sl.variety
               FROM germination_tests gt
               JOIN seed_lots sl ON gt.lot_id = sl.id
               ORDER BY gt.date_tested DESC"""
        )
    for row in rows:
        if row["sample_size"] > 0:
            row["germination_rate"] = round(row["germination_count"] / row["sample_size"] * 100, 1)
        else:
            row["germination_rate"] = 0
    return rows


@router.get("/tests/{test_id}")
def get_test(test_id: int) -> dict:
    results = query(
        """SELECT gt.*, sl.name as lot_name, sl.species, sl.variety
           FROM germination_tests gt
           JOIN seed_lots sl ON gt.lot_id = sl.id
           WHERE gt.id = ?""",
        (test_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Germination test not found")
    result = results[0]
    if result["sample_size"] > 0:
        result["germination_rate"] = round(result["germination_count"] / result["sample_size"] * 100, 1)
    return result


@router.get("/history/{species}")
def species_history(species: str) -> list[dict]:
    rows = query(
        """SELECT gt.*, sl.name as lot_name, sl.variety
           FROM germination_tests gt
           JOIN seed_lots sl ON gt.lot_id = sl.id
           WHERE sl.species = ?
           ORDER BY gt.date_tested DESC""",
        (species,),
    )
    for row in rows:
        if row["sample_size"] > 0:
            row["germination_rate"] = round(row["germination_count"] / row["sample_size"] * 100, 1)
    return rows


@router.get("/reminders")
def test_reminders() -> list[dict]:
    """Return lots that haven't been tested in over 365 days or never tested."""
    return query("""
        SELECT sl.*, MAX(gt.date_tested) as last_tested,
               CAST(julianday('now') - julianday(COALESCE(MAX(gt.date_tested), sl.date_collected)) AS INTEGER) as days_since_test
        FROM seed_lots sl
        LEFT JOIN germination_tests gt ON sl.id = gt.lot_id
        GROUP BY sl.id
        HAVING days_since_test >= 365 OR last_tested IS NULL
        ORDER BY days_since_test DESC
    """)
