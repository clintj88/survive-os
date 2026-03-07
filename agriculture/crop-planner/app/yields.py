"""Yield tracking and prediction for the crop planner."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/yields", tags=["yields"])


class YieldRecord(BaseModel):
    plot_id: int
    crop_id: int
    year: int
    season: str
    amount: float
    unit: str = "kg"
    notes: str = ""


@router.get("")
def list_yields(
    plot_id: Optional[int] = Query(None),
    crop_id: Optional[int] = Query(None),
) -> list[dict]:
    conditions = []
    params: list = []
    if plot_id is not None:
        conditions.append("y.plot_id = ?")
        params.append(plot_id)
    if crop_id is not None:
        conditions.append("y.crop_id = ?")
        params.append(crop_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT y.*, c.name as crop_name, p.label as plot_label
            FROM yields y
            JOIN crops c ON y.crop_id = c.id
            JOIN plots p ON y.plot_id = p.id
            {where}
            ORDER BY y.year DESC, y.season""",
        tuple(params),
    )


@router.post("", status_code=201)
def record_yield(record: YieldRecord) -> dict:
    yield_id = execute(
        """INSERT INTO yields (plot_id, crop_id, year, season, amount, unit, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (record.plot_id, record.crop_id, record.year, record.season,
         record.amount, record.unit, record.notes),
    )
    results = query(
        """SELECT y.*, c.name as crop_name, p.label as plot_label
           FROM yields y
           JOIN crops c ON y.crop_id = c.id
           JOIN plots p ON y.plot_id = p.id
           WHERE y.id = ?""",
        (yield_id,),
    )
    return results[0]


@router.get("/predict")
def predict_yield(plot_id: int, crop_id: int) -> dict:
    """Predict yield using simple moving average of historical data."""
    history = query(
        """SELECT amount, unit, year, season FROM yields
           WHERE plot_id = ? AND crop_id = ?
           ORDER BY year DESC, season
           LIMIT 10""",
        (plot_id, crop_id),
    )

    crop = query("SELECT name FROM crops WHERE id = ?", (crop_id,))
    crop_name = crop[0]["name"] if crop else "Unknown"

    if not history:
        return {
            "plot_id": plot_id,
            "crop_id": crop_id,
            "crop_name": crop_name,
            "predicted_yield": None,
            "confidence": "none",
            "message": "No historical yield data available",
        }

    amounts = [h["amount"] for h in history]
    unit = history[0]["unit"]
    avg = sum(amounts) / len(amounts)

    # Simple trend: compare recent half vs older half
    if len(amounts) >= 4:
        mid = len(amounts) // 2
        recent_avg = sum(amounts[:mid]) / mid
        older_avg = sum(amounts[mid:]) / (len(amounts) - mid)
        trend = recent_avg - older_avg
        prediction = avg + trend * 0.5
        confidence = "medium" if len(amounts) >= 6 else "low"
    else:
        prediction = avg
        trend = 0.0
        confidence = "low"

    return {
        "plot_id": plot_id,
        "crop_id": crop_id,
        "crop_name": crop_name,
        "predicted_yield": round(max(0, prediction), 2),
        "unit": unit,
        "average_yield": round(avg, 2),
        "trend": round(trend, 2),
        "data_points": len(amounts),
        "confidence": confidence,
        "history": history,
    }
