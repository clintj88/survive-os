"""Planting window advisor based on weather patterns."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .database import execute, query

logger = logging.getLogger("survive-weather.planting")


def record_frost_date(year: int, frost_type: str, frost_date: str) -> dict:
    """Record a frost date (last_spring or first_fall)."""
    execute(
        """INSERT INTO frost_dates (year, frost_type, frost_date)
           VALUES (?, ?, ?)
           ON CONFLICT(year, frost_type)
           DO UPDATE SET frost_date = excluded.frost_date""",
        (year, frost_type, frost_date),
    )
    results = query(
        "SELECT * FROM frost_dates WHERE year = ? AND frost_type = ?",
        (year, frost_type),
    )
    return results[0] if results else {}


def get_frost_dates(year: Optional[int] = None) -> list[dict]:
    """Get frost dates, optionally filtered by year."""
    if year:
        return query(
            "SELECT * FROM frost_dates WHERE year = ? ORDER BY frost_type",
            (year,),
        )
    return query("SELECT * FROM frost_dates ORDER BY year DESC, frost_type")


def get_growing_season(year: int, config: dict[str, Any]) -> dict[str, Any]:
    """Calculate growing season length for a year."""
    frost = query(
        "SELECT frost_type, frost_date FROM frost_dates WHERE year = ?",
        (year,),
    )
    frost_map = {f["frost_type"]: f["frost_date"] for f in frost}

    last_spring = frost_map.get(
        "last_spring",
        f"{year}-{config.get('frost', {}).get('avg_last_spring', '04-15')}",
    )
    first_fall = frost_map.get(
        "first_fall",
        f"{year}-{config.get('frost', {}).get('avg_first_fall', '10-15')}",
    )

    # Ensure full date format
    if len(last_spring) <= 5:
        last_spring = f"{year}-{last_spring}"
    if len(first_fall) <= 5:
        first_fall = f"{year}-{first_fall}"

    try:
        spring_dt = datetime.strptime(last_spring, "%Y-%m-%d")
        fall_dt = datetime.strptime(first_fall, "%Y-%m-%d")
        days = (fall_dt - spring_dt).days
    except ValueError:
        days = 0

    return {
        "year": year,
        "last_spring_frost": last_spring,
        "first_fall_frost": first_fall,
        "growing_season_days": max(days, 0),
        "source": "recorded" if frost else "config_default",
    }


def get_planting_windows(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Calculate planting windows based on frost dates and weather patterns."""
    year = datetime.now(timezone.utc).year
    season = get_growing_season(year, config)

    try:
        spring = datetime.strptime(season["last_spring_frost"], "%Y-%m-%d")
        fall = datetime.strptime(season["first_fall_frost"], "%Y-%m-%d")
    except ValueError:
        return []

    windows = [
        {
            "crop_type": "cool_season_early",
            "label": "Cool Season (Early) - Peas, Lettuce, Spinach",
            "start": (spring - timedelta(days=14)).strftime("%Y-%m-%d"),
            "end": (spring + timedelta(days=14)).strftime("%Y-%m-%d"),
            "notes": "Can tolerate light frost",
        },
        {
            "crop_type": "warm_season",
            "label": "Warm Season - Tomatoes, Peppers, Beans",
            "start": (spring + timedelta(days=14)).strftime("%Y-%m-%d"),
            "end": (spring + timedelta(days=42)).strftime("%Y-%m-%d"),
            "notes": "After last frost, soil above 15C",
        },
        {
            "crop_type": "hot_season",
            "label": "Hot Season - Melons, Squash, Corn",
            "start": (spring + timedelta(days=28)).strftime("%Y-%m-%d"),
            "end": (spring + timedelta(days=56)).strftime("%Y-%m-%d"),
            "notes": "Soil above 20C, long growing season needed",
        },
        {
            "crop_type": "fall_planting",
            "label": "Fall Planting - Garlic, Cover Crops",
            "start": (fall - timedelta(days=42)).strftime("%Y-%m-%d"),
            "end": (fall - timedelta(days=14)).strftime("%Y-%m-%d"),
            "notes": "Before first fall frost",
        },
    ]

    return windows


def publish_advisory(message: str, advisory_type: str, redis_client: Any = None) -> int:
    """Create and publish a planting advisory."""
    advisory_id = execute(
        """INSERT INTO planting_advisories (advisory_type, message)
           VALUES (?, ?)""",
        (advisory_type, message),
    )

    if redis_client:
        try:
            payload = json.dumps({
                "type": advisory_type,
                "message": message,
                "source": "weather-planting",
            })
            redis_client.publish("agriculture.weather-advisory", payload)
            logger.info("Published planting advisory: %s", advisory_type)
        except Exception as e:
            logger.error("Failed to publish advisory to Redis: %s", e)

    return advisory_id


def get_advisories(limit: int = 20) -> list[dict]:
    """Get recent planting advisories."""
    return query(
        "SELECT * FROM planting_advisories ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
