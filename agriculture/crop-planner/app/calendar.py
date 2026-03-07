"""Planting calendar for the crop planner."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter

from .config import load_config
from .database import query

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

config = load_config()


def _parse_frost_date(md_str: str, year: int) -> date:
    """Parse a MM-DD string into a date for the given year."""
    month, day = md_str.split("-")
    return date(year, int(month), int(day))


def _get_frost_dates(year: int) -> tuple[date, date]:
    """Get last spring frost and first fall frost dates."""
    last_spring = _parse_frost_date(config["frost_dates"]["last_spring"], year)
    first_fall = _parse_frost_date(config["frost_dates"]["first_fall"], year)
    return last_spring, first_fall


@router.get("/frost-dates")
def get_frost_dates(year: int = 2026) -> dict:
    last_spring, first_fall = _get_frost_dates(year)
    growing_days = (first_fall - last_spring).days
    return {
        "year": year,
        "last_spring_frost": last_spring.isoformat(),
        "first_fall_frost": first_fall.isoformat(),
        "growing_season_days": growing_days,
    }


@router.get("/planting-windows")
def get_planting_windows(year: int = 2026) -> list[dict]:
    """Get planting windows for all crops based on frost dates."""
    last_spring, first_fall = _get_frost_dates(year)
    crops = query("SELECT * FROM crops ORDER BY name")

    windows = []
    for crop in crops:
        window: dict = {
            "crop_id": crop["id"],
            "crop_name": crop["name"],
            "year": year,
        }
        if crop["sow_indoor_offset"] is not None:
            d = last_spring + timedelta(days=crop["sow_indoor_offset"])
            window["sow_indoor"] = d.isoformat()
        if crop["sow_outdoor_offset"] is not None:
            d = last_spring + timedelta(days=crop["sow_outdoor_offset"])
            window["sow_outdoor"] = d.isoformat()
        if crop["transplant_offset"] is not None:
            d = last_spring + timedelta(days=crop["transplant_offset"])
            window["transplant"] = d.isoformat()
        if crop["harvest_start_offset"] is not None:
            d = last_spring + timedelta(days=crop["harvest_start_offset"])
            window["harvest_start"] = d.isoformat()
        if crop["harvest_end_offset"] is not None:
            d = last_spring + timedelta(days=crop["harvest_end_offset"])
            window["harvest_end"] = d.isoformat()

        window["days_to_maturity"] = crop["days_to_maturity"]
        windows.append(window)

    return windows


@router.get("/planting-windows/{crop_id}")
def get_crop_planting_window(crop_id: int, year: int = 2026) -> dict:
    """Get planting window for a specific crop."""
    crops = query("SELECT * FROM crops WHERE id = ?", (crop_id,))
    if not crops:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Crop not found")

    crop = crops[0]
    last_spring, first_fall = _get_frost_dates(year)

    window: dict = {
        "crop_id": crop["id"],
        "crop_name": crop["name"],
        "year": year,
        "days_to_maturity": crop["days_to_maturity"],
    }
    if crop["sow_indoor_offset"] is not None:
        d = last_spring + timedelta(days=crop["sow_indoor_offset"])
        window["sow_indoor"] = d.isoformat()
    if crop["sow_outdoor_offset"] is not None:
        d = last_spring + timedelta(days=crop["sow_outdoor_offset"])
        window["sow_outdoor"] = d.isoformat()
    if crop["transplant_offset"] is not None:
        d = last_spring + timedelta(days=crop["transplant_offset"])
        window["transplant"] = d.isoformat()
    if crop["harvest_start_offset"] is not None:
        d = last_spring + timedelta(days=crop["harvest_start_offset"])
        window["harvest_start"] = d.isoformat()
    if crop["harvest_end_offset"] is not None:
        d = last_spring + timedelta(days=crop["harvest_end_offset"])
        window["harvest_end"] = d.isoformat()

    return window


@router.get("/month/{year}/{month}")
def get_month_events(year: int, month: int) -> list[dict]:
    """Get all planting events for a given month."""
    last_spring, _ = _get_frost_dates(year)
    crops = query("SELECT * FROM crops ORDER BY name")

    events = []
    for crop in crops:
        offset_fields = [
            ("sow_indoor_offset", "Sow Indoors"),
            ("sow_outdoor_offset", "Sow Outdoors"),
            ("transplant_offset", "Transplant"),
            ("harvest_start_offset", "Harvest Begins"),
            ("harvest_end_offset", "Harvest Ends"),
        ]
        for field, label in offset_fields:
            offset = crop[field]
            if offset is not None:
                event_date = last_spring + timedelta(days=offset)
                if event_date.year == year and event_date.month == month:
                    events.append({
                        "date": event_date.isoformat(),
                        "crop_id": crop["id"],
                        "crop_name": crop["name"],
                        "event": label,
                    })

    events.sort(key=lambda e: e["date"])
    return events
