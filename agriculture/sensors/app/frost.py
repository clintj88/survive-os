"""Frost detection and alerting."""

import json
import logging
from typing import Any, Optional

from .database import execute, query

logger = logging.getLogger("survive-sensors.frost")

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class FrostMonitor:
    """Monitor temperature readings and issue frost alerts."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.threshold_c = config["frost"]["threshold_c"]
        self.redis_url = config["redis"]["url"]
        self.frost_channel = config["redis"]["frost_alert_channel"]
        self.comms_channel = config["redis"]["comms_alert_channel"]
        self._redis: Optional[Any] = None

    async def connect(self) -> bool:
        if not HAS_REDIS:
            return False
        try:
            self._redis = aioredis.from_url(self.redis_url)
            await self._redis.ping()
            return True
        except Exception:
            logger.exception("Frost monitor: failed to connect to Redis")
            self._redis = None
            return False

    async def stop(self) -> None:
        if self._redis:
            await self._redis.close()

    def _get_trend(self, node_id: str) -> str:
        """Determine temperature trend from recent readings."""
        rows = query(
            """SELECT temperature_c FROM weather_readings
               WHERE node_id = ? AND temperature_c IS NOT NULL
               ORDER BY timestamp DESC LIMIT 3""",
            (node_id,),
        )
        if len(rows) < 2:
            return "unknown"
        temps = [r["temperature_c"] for r in rows]
        # temps[0] is most recent
        if temps[0] < temps[1]:
            return "falling"
        elif temps[0] > temps[1]:
            return "rising"
        return "stable"

    async def check_reading(self, data: dict[str, Any]) -> Optional[dict]:
        """Check a weather reading for frost conditions. Returns alert dict if triggered."""
        temp = data.get("temperature_c")
        if temp is None or temp > self.threshold_c:
            return None

        node_id = data["node_id"]
        location = data.get("location", "")

        # Look up location from node registry if not in data
        if not location:
            from .nodes import get_node
            node = get_node(node_id)
            if node:
                location = node.get("location", "")

        trend = self._get_trend(node_id)

        alert = {
            "type": "frost-alert",
            "node_id": node_id,
            "location": location,
            "temperature_c": temp,
            "trend": trend,
            "threshold_c": self.threshold_c,
        }

        # Store alert
        execute(
            """INSERT INTO frost_alerts (node_id, location, temperature_c, trend)
               VALUES (?, ?, ?, ?)""",
            (node_id, location, temp, trend),
        )

        # Publish to Redis
        await self._publish_alert(alert)

        logger.warning("Frost alert: %.1f°C at %s (node %s, %s)",
                        temp, location, node_id, trend)
        return alert

    async def _publish_alert(self, alert: dict) -> None:
        if not self._redis:
            return
        payload = json.dumps(alert)
        try:
            await self._redis.publish(self.frost_channel, payload)
            await self._redis.publish(self.comms_channel, payload)
        except Exception:
            logger.exception("Failed to publish frost alert")

    def get_recent_alerts(self, limit: int = 50) -> list[dict]:
        return query(
            "SELECT * FROM frost_alerts ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
