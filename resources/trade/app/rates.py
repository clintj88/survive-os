"""Exchange rate management for the trade/barter system."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/rates", tags=["rates"])


class RateCreate(BaseModel):
    commodity_a: str
    commodity_b: str
    rate: float
    set_by: str = "system"


class RateUpdate(BaseModel):
    rate: Optional[float] = None
    set_by: Optional[str] = None


@router.get("")
def list_rates(commodity: Optional[str] = None) -> list[dict]:
    if commodity:
        return query(
            """SELECT id, commodity_a, commodity_b, rate, set_by,
                      effective_date, created_at
               FROM exchange_rates
               WHERE commodity_a = ? OR commodity_b = ?
               ORDER BY effective_date DESC""",
            (commodity, commodity),
        )
    return query(
        """SELECT id, commodity_a, commodity_b, rate, set_by,
                  effective_date, created_at
           FROM exchange_rates
           ORDER BY effective_date DESC"""
    )


@router.get("/current")
def current_rates() -> list[dict]:
    """Get the most recent rate for each commodity pair."""
    return query(
        """SELECT r.id, r.commodity_a, r.commodity_b, r.rate, r.set_by,
                  r.effective_date, r.created_at
           FROM exchange_rates r
           INNER JOIN (
               SELECT commodity_a, commodity_b, MAX(id) as max_id
               FROM exchange_rates
               GROUP BY commodity_a, commodity_b
           ) latest ON r.id = latest.max_id
           ORDER BY r.commodity_a"""
    )


@router.get("/{rate_id}")
def get_rate(rate_id: int) -> dict:
    results = query(
        """SELECT id, commodity_a, commodity_b, rate, set_by,
                  effective_date, created_at
           FROM exchange_rates WHERE id = ?""",
        (rate_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Rate not found")
    return results[0]


@router.post("", status_code=201)
def create_rate(rate: RateCreate) -> dict:
    if rate.rate <= 0:
        raise HTTPException(status_code=400, detail="Rate must be positive")
    rate_id = execute(
        """INSERT INTO exchange_rates (commodity_a, commodity_b, rate, set_by)
           VALUES (?, ?, ?, ?)""",
        (rate.commodity_a, rate.commodity_b, rate.rate, rate.set_by),
    )
    return get_rate(rate_id)


@router.get("/history/{commodity_a}/{commodity_b}")
def rate_history(commodity_a: str, commodity_b: str) -> list[dict]:
    return query(
        """SELECT id, commodity_a, commodity_b, rate, set_by,
                  effective_date, created_at
           FROM exchange_rates
           WHERE commodity_a = ? AND commodity_b = ?
           ORDER BY effective_date DESC""",
        (commodity_a, commodity_b),
    )


@router.get("/convert/{commodity_a}/{commodity_b}")
def convert(commodity_a: str, commodity_b: str, amount: float = 1.0) -> dict:
    """Convert an amount from commodity_a to commodity_b using the latest rate."""
    results = query(
        """SELECT rate FROM exchange_rates
           WHERE commodity_a = ? AND commodity_b = ?
           ORDER BY effective_date DESC LIMIT 1""",
        (commodity_a, commodity_b),
    )
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No rate found for {commodity_a} -> {commodity_b}",
        )
    rate = results[0]["rate"]
    return {
        "from": commodity_a,
        "to": commodity_b,
        "amount": amount,
        "rate": rate,
        "result": amount * rate,
    }
