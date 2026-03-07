"""Weather Station API - SURVIVE OS Weather Module."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .observations import router as observations_router
from . import analysis, planting, sensors, storms, trends

config = load_config()
VERSION = config["version"]
logger = logging.getLogger("survive-weather")

_redis_client: Any = None
_sensor_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _redis_client, _sensor_task
    set_db_path(config["database"]["path"])
    init_db()

    # Try to connect to Redis for pub/sub
    try:
        import redis
        _redis_client = redis.from_url(config["redis"]["url"])
        _redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning("Redis unavailable, running without pub/sub: %s", e)
        _redis_client = None

    # Start sensor listener in background
    try:
        _sensor_task = asyncio.create_task(
            sensors.start_sensor_listener(config["redis"]["url"])
        )
    except Exception as e:
        logger.warning("Could not start sensor listener: %s", e)

    yield

    # Cleanup
    if _sensor_task:
        _sensor_task.cancel()
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass


app = FastAPI(title="SURVIVE OS Weather Station", version=VERSION, lifespan=lifespan)

# Include observation CRUD router
app.include_router(observations_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# --- Analysis / Forecast endpoints ---

@app.get("/api/forecast")
def get_forecast() -> dict:
    return analysis.generate_forecast()


@app.get("/api/analysis/averages")
def get_averages() -> dict:
    return analysis.get_all_moving_averages()


@app.get("/api/analysis/pressure")
def get_pressure() -> dict:
    return analysis.get_pressure_trends()


@app.get("/api/analysis/seasonal-normals")
def get_seasonal_normals() -> list[dict]:
    return analysis.get_seasonal_normals()


# --- Planting endpoints ---

@app.get("/api/planting/frost-dates")
def get_frost_dates(year: Optional[int] = Query(None)) -> list[dict]:
    return planting.get_frost_dates(year)


@app.post("/api/planting/frost-dates", status_code=201)
def record_frost_date(year: int, frost_type: str, frost_date: str) -> dict:
    return planting.record_frost_date(year, frost_type, frost_date)


@app.get("/api/planting/growing-season")
def get_growing_season(year: int = Query(...)) -> dict:
    return planting.get_growing_season(year, config)


@app.get("/api/planting/windows")
def get_planting_windows() -> list[dict]:
    return planting.get_planting_windows(config)


@app.get("/api/planting/advisories")
def get_advisories(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
    return planting.get_advisories(limit)


@app.post("/api/planting/advisories", status_code=201)
def create_advisory(message: str, advisory_type: str = "general") -> dict:
    advisory_id = planting.publish_advisory(message, advisory_type, _redis_client)
    return {"id": advisory_id, "message": message, "type": advisory_type}


# --- Storm endpoints ---

@app.get("/api/storms/active")
def get_active_storms() -> list[dict]:
    return storms.get_active_storms()


@app.get("/api/storms/history")
def get_storm_history(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    return storms.get_storm_history(limit)


@app.post("/api/storms/check")
def check_storms() -> list[dict]:
    return storms.check_and_alert(config, _redis_client)


@app.post("/api/storms/{event_id}/end")
def end_storm(event_id: int, total_precip_mm: float = 0) -> dict:
    storms.end_storm_event(event_id, total_precip_mm)
    return {"status": "ended", "event_id": event_id}


# --- Trends endpoints ---

@app.get("/api/trends/monthly")
def get_monthly(year: Optional[int] = Query(None)) -> list[dict]:
    return trends.get_monthly_averages(year)


@app.get("/api/trends/seasonal")
def get_seasonal(year: Optional[int] = Query(None)) -> list[dict]:
    return trends.get_seasonal_averages(year)


@app.get("/api/trends/annual")
def get_annual(year: Optional[int] = Query(None)) -> list[dict]:
    return trends.get_annual_summary(year)


@app.get("/api/trends/year-over-year")
def get_yoy(month: int = Query(..., ge=1, le=12)) -> list[dict]:
    return trends.get_year_over_year(month)


@app.get("/api/trends/gdd")
def get_gdd(
    base_temp: float = Query(10.0),
    year: Optional[int] = Query(None),
) -> dict:
    return trends.get_growing_degree_days(base_temp, year)


@app.get("/api/trends/rainfall")
def get_rainfall(year: Optional[int] = Query(None)) -> list[dict]:
    return trends.get_rainfall_by_season(year)


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
