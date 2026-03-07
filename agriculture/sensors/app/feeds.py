"""Data feeds to other SURVIVE OS modules."""

import json
import logging
from typing import Any, Optional

from .database import query

logger = logging.getLogger("survive-sensors.feeds")

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class DataFeed:
    """Publish aggregated sensor data for consumption by other modules."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.redis_url = config["redis"]["url"]
        self.weather_channel = config["redis"]["weather_channel"]
        self._redis: Optional[Any] = None

    async def connect(self) -> bool:
        if not HAS_REDIS:
            return False
        try:
            self._redis = aioredis.from_url(self.redis_url)
            await self._redis.ping()
            return True
        except Exception:
            logger.exception("DataFeed: failed to connect to Redis")
            self._redis = None
            return False

    async def stop(self) -> None:
        if self._redis:
            await self._redis.close()

    async def publish_weather_observation(self, data: dict[str, Any]) -> None:
        """Publish a weather observation to the weather channel."""
        if not self._redis:
            return
        observation = {
            "source": "agriculture-sensors",
            "node_id": data.get("node_id"),
            "temperature_c": data.get("temperature_c"),
            "humidity_pct": data.get("humidity_pct"),
            "pressure_hpa": data.get("pressure_hpa"),
            "timestamp": data.get("timestamp"),
        }
        try:
            await self._redis.publish(self.weather_channel, json.dumps(observation))
        except Exception:
            logger.exception("Failed to publish weather observation")

    def get_latest_readings(self) -> dict[str, Any]:
        """Get latest readings from all sensor types for the dashboard."""
        weather = query(
            """SELECT w.*, n.name as node_name, n.location
               FROM weather_readings w
               JOIN nodes n ON w.node_id = n.node_id
               WHERE w.id IN (
                   SELECT MAX(id) FROM weather_readings GROUP BY node_id
               )
               ORDER BY w.timestamp DESC"""
        )
        soil = query(
            """SELECT s.*, n.name as node_name, n.location
               FROM soil_readings s
               JOIN nodes n ON s.node_id = n.node_id
               WHERE s.id IN (
                   SELECT MAX(id) FROM soil_readings GROUP BY node_id
               )
               ORDER BY s.timestamp DESC"""
        )
        rain = query(
            """SELECT r.*, n.name as node_name, n.location
               FROM rain_readings r
               JOIN nodes n ON r.node_id = n.node_id
               WHERE r.id IN (
                   SELECT MAX(id) FROM rain_readings GROUP BY node_id
               )
               ORDER BY r.timestamp DESC"""
        )
        return {"weather": weather, "soil": soil, "rain": rain}
