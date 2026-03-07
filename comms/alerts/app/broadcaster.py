"""Multi-tier alert broadcaster via Redis pub/sub."""

import json
import logging
from typing import Any

logger = logging.getLogger("survive-alerts")

_redis_client = None


def init_redis(host: str = "localhost", port: int = 6379) -> None:
    """Initialize Redis connection. Fails gracefully if Redis unavailable."""
    global _redis_client
    try:
        import redis
        _redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        _redis_client.ping()
        logger.info("Connected to Redis at %s:%d", host, port)
    except Exception as e:
        logger.warning("Redis unavailable (%s), broadcast will log locally only", e)
        _redis_client = None


def broadcast_alert(
    alert_data: dict[str, Any],
    channels: list[str],
) -> list[dict[str, Any]]:
    """Broadcast alert to all configured channels. Returns broadcast log entries."""
    results = []
    payload = json.dumps(alert_data)

    for channel in channels:
        entry: dict[str, Any] = {
            "alert_id": alert_data["id"],
            "channel": channel,
        }
        if _redis_client is not None:
            try:
                _redis_client.publish(channel, payload)
                entry["status"] = "sent"
            except Exception as e:
                logger.error("Failed to broadcast to %s: %s", channel, e)
                entry["status"] = "failed"
                entry["error"] = str(e)
        else:
            logger.info("Broadcast (local-only) to %s: %s", channel, payload)
            entry["status"] = "local_only"

        results.append(entry)

    return results
