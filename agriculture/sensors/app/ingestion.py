"""Data ingestion from Meshtastic mesh network via Redis pub/sub."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .database import execute, query
from .nodes import touch_node

logger = logging.getLogger("survive-sensors.ingestion")

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class SensorIngestion:
    """Subscribe to Meshtastic messages and ingest sensor data."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.redis_url = config["redis"]["url"]
        self.subscribe_channel = config["redis"]["subscribe_channel"]
        self.retention_days = config["data_retention"]["days"]
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._on_reading: Optional[Any] = None

    def set_reading_callback(self, callback: Any) -> None:
        """Set callback invoked with (reading_type, data) on each ingested reading."""
        self._on_reading = callback

    async def connect(self) -> bool:
        if not HAS_REDIS:
            logger.warning("redis library not installed, ingestion disabled")
            return False
        try:
            self._redis = aioredis.from_url(self.redis_url)
            await self._redis.ping()
            logger.info("Connected to Redis at %s", self.redis_url)
            return True
        except Exception:
            logger.exception("Failed to connect to Redis")
            self._redis = None
            return False

    async def start(self) -> None:
        if not self._redis:
            return
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.subscribe_channel)
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("Listening on channel: %s", self.subscribe_channel)

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe(self.subscribe_channel)
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("Ingestion stopped")

    async def _listen(self) -> None:
        try:
            async for raw_message in self._pubsub.listen():
                if raw_message["type"] != "message":
                    continue
                try:
                    data = json.loads(raw_message["data"])
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON: %s", raw_message["data"])
                except Exception:
                    logger.exception("Error processing message")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Ingestion listener error")

    async def _process_message(self, data: dict[str, Any]) -> None:
        """Route incoming sensor data to the appropriate handler."""
        node_id = data.get("node_id")
        sensor_type = data.get("type")
        if not node_id or not sensor_type:
            return

        touch_node(
            node_id,
            battery_level=data.get("battery_level"),
            firmware_version=data.get("firmware_version"),
        )

        ts = data.get("timestamp", datetime.now(timezone.utc).isoformat())

        if sensor_type == "soil":
            self._store_soil(node_id, data, ts)
        elif sensor_type == "weather":
            self._store_weather(node_id, data, ts)
        elif sensor_type == "rain":
            self._store_rain(node_id, data, ts)
        else:
            logger.debug("Unknown sensor type: %s", sensor_type)
            return

        if self._on_reading:
            await self._on_reading(sensor_type, data)

    def _store_soil(self, node_id: str, data: dict, ts: str) -> None:
        execute(
            """INSERT INTO soil_readings (node_id, moisture_pct, depth_cm,
               temperature_c, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (node_id, data.get("moisture_pct", 0), data.get("depth_cm"),
             data.get("temperature_c"), ts),
        )

    def _store_weather(self, node_id: str, data: dict, ts: str) -> None:
        execute(
            """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct,
               pressure_hpa, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (node_id, data.get("temperature_c"), data.get("humidity_pct"),
             data.get("pressure_hpa"), ts),
        )

    def _store_rain(self, node_id: str, data: dict, ts: str) -> None:
        execute(
            """INSERT INTO rain_readings (node_id, rainfall_mm, period_minutes,
               timestamp)
               VALUES (?, ?, ?, ?)""",
            (node_id, data.get("rainfall_mm", 0), data.get("period_minutes"), ts),
        )

    def prune_old_data(self) -> int:
        """Delete readings older than retention period. Returns count deleted."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        total = 0
        for table in ("soil_readings", "weather_readings", "rain_readings"):
            rows = query(f"SELECT COUNT(*) as cnt FROM {table} WHERE timestamp < ?", (cutoff,))
            count = rows[0]["cnt"] if rows else 0
            if count > 0:
                execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))
                total += count
        return total
