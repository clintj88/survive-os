"""Sensor data ingestion from Redis pub/sub."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .database import execute, query

logger = logging.getLogger("survive-weather.sensors")

# Outlier thresholds
TEMP_MIN, TEMP_MAX = -60.0, 60.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
PRESSURE_MIN, PRESSURE_MAX = 870.0, 1084.0
RAINFALL_MIN, RAINFALL_MAX = 0.0, 500.0


def validate_sensor_reading(data: dict[str, Any]) -> dict[str, Any]:
    """Validate sensor data and flag outliers. Returns cleaned data."""
    cleaned: dict[str, Any] = {}
    warnings: list[str] = []

    if "temperature_c" in data:
        t = float(data["temperature_c"])
        if TEMP_MIN <= t <= TEMP_MAX:
            cleaned["temperature_c"] = t
        else:
            warnings.append(f"Temperature {t}C out of range [{TEMP_MIN}, {TEMP_MAX}]")

    if "humidity_pct" in data:
        h = float(data["humidity_pct"])
        if HUMIDITY_MIN <= h <= HUMIDITY_MAX:
            cleaned["humidity_pct"] = h
        else:
            warnings.append(f"Humidity {h}% out of range")

    if "pressure_hpa" in data:
        p = float(data["pressure_hpa"])
        if PRESSURE_MIN <= p <= PRESSURE_MAX:
            cleaned["pressure_hpa"] = p
        else:
            warnings.append(f"Pressure {p}hPa out of range")

    if "rainfall_mm" in data:
        r = float(data["rainfall_mm"])
        if RAINFALL_MIN <= r <= RAINFALL_MAX:
            cleaned["rainfall_mm"] = r
        else:
            warnings.append(f"Rainfall {r}mm out of range")

    if warnings:
        logger.warning("Sensor validation warnings: %s", "; ".join(warnings))

    return cleaned


def ingest_sensor_data(data: dict[str, Any]) -> Optional[int]:
    """Ingest a sensor reading into the database. Returns observation id or None."""
    cleaned = validate_sensor_reading(data)
    if not cleaned:
        logger.warning("No valid fields in sensor data: %s", data)
        return None

    observed_at = data.get("timestamp", datetime.now(timezone.utc).isoformat())

    obs_id = execute(
        """INSERT INTO observations
           (observed_at, observer, source, temperature_c, humidity_pct,
            pressure_hpa, rainfall_mm)
           VALUES (?, ?, 'sensor', ?, ?, ?, ?)""",
        (
            observed_at,
            data.get("sensor_id", "auto-sensor"),
            cleaned.get("temperature_c"),
            cleaned.get("humidity_pct"),
            cleaned.get("pressure_hpa"),
            cleaned.get("rainfall_mm", 0),
        ),
    )
    return obs_id


async def start_sensor_listener(redis_url: str) -> None:
    """Subscribe to Redis weather.observations channel and ingest data."""
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.error("redis package not installed, sensor ingestion disabled")
        return

    try:
        client = aioredis.from_url(redis_url)
        pubsub = client.pubsub()
        await pubsub.subscribe("weather.observations")
        logger.info("Subscribed to weather.observations channel")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    ingest_sensor_data(data)
                except (json.JSONDecodeError, Exception) as e:
                    logger.error("Failed to process sensor data: %s", e)
    except Exception as e:
        logger.error("Redis connection failed: %s", e)


def get_unified_observations(
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Get merged manual and sensor observations."""
    conditions: list[str] = []
    params: list = []
    if start:
        conditions.append("observed_at >= ?")
        params.append(start)
    if end:
        conditions.append("observed_at <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    return query(
        f"SELECT * FROM observations {where} ORDER BY observed_at DESC LIMIT ?",
        tuple(params),
    )
