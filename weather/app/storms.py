"""Storm detection and alert system."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .database import execute, query

logger = logging.getLogger("survive-weather.storms")

REDIS_ALERT_CHANNELS = ["comms.alerts", "comms.ham-radio", "comms.meshtastic"]


def detect_storms(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze current conditions for storm indicators."""
    alerts_config = config.get("alerts", {})
    pressure_threshold = alerts_config.get("pressure_drop_threshold_hpa", 3.0)
    pressure_window = alerts_config.get("pressure_drop_window_hours", 3)
    wind_threshold = alerts_config.get("high_wind_kph", 60)
    temp_drop_threshold = alerts_config.get("temp_drop_threshold_c", 8.0)
    temp_window = alerts_config.get("temp_drop_window_hours", 3)

    detected: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    # Check pressure drop
    cutoff = (now - timedelta(hours=pressure_window)).isoformat()
    pressure_data = query(
        "SELECT pressure_hpa, observed_at FROM observations "
        "WHERE pressure_hpa IS NOT NULL AND observed_at >= ? "
        "ORDER BY observed_at ASC",
        (cutoff,),
    )
    if len(pressure_data) >= 2:
        first_p = pressure_data[0]["pressure_hpa"]
        last_p = pressure_data[-1]["pressure_hpa"]
        drop = first_p - last_p
        if drop >= pressure_threshold:
            severity = "emergency" if drop >= pressure_threshold * 2 else "warning"
            detected.append({
                "event_type": "pressure_drop",
                "severity": severity,
                "description": f"Rapid pressure drop: {drop:.1f} hPa in {pressure_window}h",
                "pressure_drop_hpa": round(drop, 2),
            })

    # Check high winds
    wind_data = query(
        "SELECT wind_speed_kph FROM observations "
        "WHERE wind_speed_kph IS NOT NULL "
        "ORDER BY observed_at DESC LIMIT 1"
    )
    if wind_data and wind_data[0]["wind_speed_kph"] >= wind_threshold:
        wind = wind_data[0]["wind_speed_kph"]
        severity = "emergency" if wind >= wind_threshold * 1.5 else "warning"
        detected.append({
            "event_type": "high_wind",
            "severity": severity,
            "description": f"High wind speed: {wind:.0f} kph",
            "max_wind_kph": wind,
        })

    # Check temperature drop (cold front indicator)
    temp_cutoff = (now - timedelta(hours=temp_window)).isoformat()
    temp_data = query(
        "SELECT temperature_c, observed_at FROM observations "
        "WHERE temperature_c IS NOT NULL AND observed_at >= ? "
        "ORDER BY observed_at ASC",
        (temp_cutoff,),
    )
    if len(temp_data) >= 2:
        first_t = temp_data[0]["temperature_c"]
        last_t = temp_data[-1]["temperature_c"]
        drop = first_t - last_t
        if drop >= temp_drop_threshold:
            detected.append({
                "event_type": "cold_front",
                "severity": "watch",
                "description": f"Cold front: temperature dropped {drop:.1f}C in {temp_window}h",
            })

    return detected


def create_storm_event(event: dict[str, Any]) -> int:
    """Create a storm event record."""
    return execute(
        """INSERT INTO storm_events
           (severity, event_type, description, max_wind_kph, pressure_drop_hpa)
           VALUES (?, ?, ?, ?, ?)""",
        (
            event.get("severity", "watch"),
            event["event_type"],
            event["description"],
            event.get("max_wind_kph"),
            event.get("pressure_drop_hpa"),
        ),
    )


def end_storm_event(event_id: int, total_precip_mm: float = 0) -> None:
    """Mark a storm event as ended."""
    execute(
        """UPDATE storm_events
           SET active = 0, ended_at = ?, total_precipitation_mm = ?
           WHERE id = ?""",
        (datetime.now(timezone.utc).isoformat(), total_precip_mm, event_id),
    )


def get_active_storms() -> list[dict]:
    """Get currently active storm events."""
    return query("SELECT * FROM storm_events WHERE active = 1 ORDER BY detected_at DESC")


def get_storm_history(limit: int = 50) -> list[dict]:
    """Get storm event history."""
    return query("SELECT * FROM storm_events ORDER BY detected_at DESC LIMIT ?", (limit,))


def propagate_alert(event: dict[str, Any], redis_client: Any = None) -> None:
    """Propagate storm alert to comms channels via Redis."""
    if not redis_client:
        logger.warning("No Redis client, cannot propagate storm alert")
        return

    payload = json.dumps({
        "source": "weather-storms",
        "severity": event.get("severity", "watch"),
        "event_type": event.get("event_type", "unknown"),
        "message": event.get("description", "Weather alert"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    for channel in REDIS_ALERT_CHANNELS:
        try:
            redis_client.publish(channel, payload)
            logger.info("Published alert to %s", channel)
        except Exception as e:
            logger.error("Failed to publish to %s: %s", channel, e)


def check_and_alert(config: dict[str, Any], redis_client: Any = None) -> list[dict]:
    """Run storm detection and propagate any alerts. Returns detected events."""
    events = detect_storms(config)
    for event in events:
        event_id = create_storm_event(event)
        event["id"] = event_id
        if event["severity"] in ("warning", "emergency"):
            propagate_alert(event, redis_client)
    return events
