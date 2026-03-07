"""Manual weather observation logger."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from .database import execute, query

router = APIRouter(prefix="/api/observations", tags=["observations"])

VALID_PRESSURE_FEEL = ("rising", "steady", "falling")
VALID_CLOUD_TYPES = ("cumulus", "stratus", "cirrus", "nimbus", "cumulonimbus", "clear")
VALID_PRECIPITATION = ("none", "light", "moderate", "heavy")
VALID_PRECIPITATION_TYPE = ("rain", "snow", "sleet", "hail")
VALID_VISIBILITY = ("good", "moderate", "poor")


class ObservationCreate(BaseModel):
    observed_at: str
    observer: str = "anonymous"
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    pressure_feel: Optional[str] = None
    wind_speed_kph: Optional[float] = None
    wind_direction: Optional[str] = None
    cloud_type: Optional[str] = None
    precipitation: str = "none"
    precipitation_type: Optional[str] = None
    visibility: str = "good"
    rainfall_mm: float = 0
    notes: str = ""

    @field_validator("pressure_feel")
    @classmethod
    def check_pressure_feel(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRESSURE_FEEL:
            raise ValueError(f"Must be one of {VALID_PRESSURE_FEEL}")
        return v

    @field_validator("cloud_type")
    @classmethod
    def check_cloud_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_CLOUD_TYPES:
            raise ValueError(f"Must be one of {VALID_CLOUD_TYPES}")
        return v

    @field_validator("precipitation")
    @classmethod
    def check_precipitation(cls, v: str) -> str:
        if v not in VALID_PRECIPITATION:
            raise ValueError(f"Must be one of {VALID_PRECIPITATION}")
        return v

    @field_validator("visibility")
    @classmethod
    def check_visibility(cls, v: str) -> str:
        if v not in VALID_VISIBILITY:
            raise ValueError(f"Must be one of {VALID_VISIBILITY}")
        return v


class ObservationUpdate(BaseModel):
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    pressure_feel: Optional[str] = None
    wind_speed_kph: Optional[float] = None
    wind_direction: Optional[str] = None
    cloud_type: Optional[str] = None
    precipitation: Optional[str] = None
    precipitation_type: Optional[str] = None
    visibility: Optional[str] = None
    rainfall_mm: Optional[float] = None
    notes: Optional[str] = None


@router.get("")
def list_observations(
    start: Optional[str] = Query(None, description="Start date (ISO format)"),
    end: Optional[str] = Query(None, description="End date (ISO format)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if start:
        conditions.append("observed_at >= ?")
        params.append(start)
    if end:
        conditions.append("observed_at <= ?")
        params.append(end)
    if source:
        conditions.append("source = ?")
        params.append(source)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    return query(
        f"SELECT * FROM observations {where} ORDER BY observed_at DESC LIMIT ?",
        tuple(params),
    )


@router.get("/latest")
def latest_observation() -> dict:
    results = query("SELECT * FROM observations ORDER BY observed_at DESC LIMIT 1")
    if not results:
        raise HTTPException(status_code=404, detail="No observations recorded")
    return results[0]


@router.get("/{observation_id}")
def get_observation(observation_id: int) -> dict:
    results = query("SELECT * FROM observations WHERE id = ?", (observation_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Observation not found")
    return results[0]


@router.post("", status_code=201)
def create_observation(obs: ObservationCreate) -> dict:
    obs_id = execute(
        """INSERT INTO observations
           (observed_at, observer, source, temperature_c, humidity_pct, pressure_hpa,
            pressure_feel, wind_speed_kph, wind_direction, cloud_type, precipitation,
            precipitation_type, visibility, rainfall_mm, notes)
           VALUES (?, ?, 'manual', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            obs.observed_at, obs.observer, obs.temperature_c, obs.humidity_pct,
            obs.pressure_hpa, obs.pressure_feel, obs.wind_speed_kph,
            obs.wind_direction, obs.cloud_type, obs.precipitation,
            obs.precipitation_type, obs.visibility, obs.rainfall_mm, obs.notes,
        ),
    )
    return get_observation(obs_id)


@router.put("/{observation_id}")
def update_observation(observation_id: int, obs: ObservationUpdate) -> dict:
    existing = query("SELECT id FROM observations WHERE id = ?", (observation_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Observation not found")

    updates: list[str] = []
    params: list = []
    for field, value in obs.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ?")
        params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(observation_id)
    execute(f"UPDATE observations SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_observation(observation_id)


@router.delete("/{observation_id}", status_code=204)
def delete_observation(observation_id: int) -> None:
    existing = query("SELECT id FROM observations WHERE id = ?", (observation_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Observation not found")
    execute("DELETE FROM observations WHERE id = ?", (observation_id,))
