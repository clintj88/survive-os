"""Redis pub/sub bridge for Meshtastic messages."""

import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("meshtastic-gw.redis")

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisBridge:
    """Bridges Meshtastic messages to/from Redis pub/sub."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.redis_url = config["redis"]["url"]
        self.channel = config["redis"]["channel"]
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._on_redis_message: Optional[Any] = None

    async def connect(self) -> bool:
        """Connect to Redis."""
        if not HAS_REDIS:
            logger.warning("redis library not installed, running without Redis bridge")
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

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe(self.channel)
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("Disconnected from Redis")

    async def publish(self, message: dict[str, Any]) -> bool:
        """Publish a message to the Redis channel."""
        if not self._redis:
            return False

        try:
            await self._redis.publish(self.channel, json.dumps(message))
            return True
        except Exception:
            logger.exception("Failed to publish to Redis")
            return False

    def set_message_callback(self, callback: Any) -> None:
        """Set callback for messages received from Redis."""
        self._on_redis_message = callback

    async def start_listener(self) -> None:
        """Start listening for messages on the Redis channel."""
        if not self._redis:
            return

        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.channel)
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Listen loop for Redis messages."""
        try:
            async for raw_message in self._pubsub.listen():
                if raw_message["type"] != "message":
                    continue
                try:
                    data = json.loads(raw_message["data"])
                    # Only forward messages not originating from this gateway
                    if data.get("source") != "meshtastic-gw":
                        if self._on_redis_message:
                            await self._on_redis_message(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from Redis: %s", raw_message["data"])
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Redis listener error")
