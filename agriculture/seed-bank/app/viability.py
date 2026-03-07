"""Seed viability prediction based on species decay curves and storage conditions."""

import math
from datetime import datetime

from fastapi import APIRouter

from .database import query
from seed.viability_data import VIABILITY_CURVES, get_viability_data

router = APIRouter(prefix="/api/viability", tags=["viability"])


def calculate_viability(
    species: str,
    date_collected: str,
    storage_temp: float | None = None,
    storage_humidity: float | None = None,
) -> dict:
    """Calculate predicted viability for a seed lot."""
    data = get_viability_data(species)
    if not data:
        return {
            "predicted_viability_pct": None,
            "status": "unknown",
            "years_remaining": None,
            "message": f"No viability data for species '{species}'",
        }

    collected = datetime.strptime(date_collected[:10], "%Y-%m-%d")
    age_years = (datetime.now() - collected).days / 365.25

    half_life = data["half_life_years"]

    # Adjust half-life based on storage conditions
    if storage_temp is not None and data["ideal_temp_c"] is not None:
        temp_diff = max(0, storage_temp - data["ideal_temp_c"])
        # Each 5C above ideal reduces half-life by ~20%
        half_life *= 0.8 ** (temp_diff / 5)

    if storage_humidity is not None and data["ideal_humidity_pct"] is not None:
        humid_diff = max(0, storage_humidity - data["ideal_humidity_pct"])
        # Each 10% above ideal reduces half-life by ~15%
        half_life *= 0.85 ** (humid_diff / 10)

    # Exponential decay: viability = 100 * (0.5)^(age/half_life)
    if half_life > 0:
        viability_pct = 100 * math.pow(0.5, age_years / half_life)
    else:
        viability_pct = 0

    viability_pct = max(0, min(100, round(viability_pct, 1)))

    # Calculate years remaining until viability drops below 50%
    if viability_pct > 50 and half_life > 0:
        years_to_50 = half_life - age_years
        years_remaining = max(0, round(years_to_50, 1))
    else:
        years_remaining = 0

    if viability_pct >= 70:
        status = "green"
    elif viability_pct >= 40:
        status = "yellow"
    else:
        status = "red"

    return {
        "predicted_viability_pct": viability_pct,
        "status": status,
        "years_remaining": years_remaining,
        "age_years": round(age_years, 1),
        "adjusted_half_life": round(half_life, 2),
    }


@router.get("/predict/{lot_id}")
def predict_lot_viability(lot_id: int) -> dict:
    lots = query("SELECT * FROM seed_lots WHERE id = ?", (lot_id,))
    if not lots:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Seed lot not found")
    lot = lots[0]
    viability = calculate_viability(
        lot["species"], lot["date_collected"],
        lot["storage_temp"], lot["storage_humidity"],
    )
    return {**lot, **viability}


@router.get("/dashboard")
def viability_dashboard() -> list[dict]:
    lots = query("SELECT * FROM seed_lots ORDER BY species, name")
    results = []
    for lot in lots:
        viability = calculate_viability(
            lot["species"], lot["date_collected"],
            lot["storage_temp"], lot["storage_humidity"],
        )
        results.append({**lot, **viability})
    return results


@router.get("/alerts")
def viability_alerts() -> list[dict]:
    """Return lots with yellow or red viability status."""
    lots = query("SELECT * FROM seed_lots ORDER BY species, name")
    alerts = []
    for lot in lots:
        viability = calculate_viability(
            lot["species"], lot["date_collected"],
            lot["storage_temp"], lot["storage_humidity"],
        )
        if viability["status"] in ("yellow", "red"):
            alerts.append({**lot, **viability})
    return alerts


@router.get("/species-data")
def species_viability_data() -> dict:
    return VIABILITY_CURVES
