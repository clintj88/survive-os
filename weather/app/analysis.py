"""Pattern analysis engine for weather forecasting."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .database import execute, query


def get_moving_averages(field: str, days: int) -> Optional[float]:
    """Calculate moving average for a field over N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    results = query(
        f"SELECT AVG({field}) as avg_val FROM observations "
        f"WHERE {field} IS NOT NULL AND observed_at >= ?",
        (cutoff,),
    )
    if results and results[0]["avg_val"] is not None:
        return round(results[0]["avg_val"], 2)
    return None


def get_all_moving_averages() -> dict[str, Any]:
    """Get 7-day, 30-day, and seasonal moving averages for key fields."""
    result: dict[str, Any] = {}
    for field in ("temperature_c", "pressure_hpa", "humidity_pct"):
        result[field] = {
            "7_day": get_moving_averages(field, 7),
            "30_day": get_moving_averages(field, 30),
            "seasonal": get_moving_averages(field, 90),
        }
    return result


def get_pressure_trend(hours: int) -> dict[str, Any]:
    """Analyze pressure trend over given hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    readings = query(
        "SELECT pressure_hpa, observed_at FROM observations "
        "WHERE pressure_hpa IS NOT NULL AND observed_at >= ? "
        "ORDER BY observed_at ASC",
        (cutoff,),
    )
    if len(readings) < 2:
        return {"trend": "insufficient_data", "change_hpa": 0, "readings": len(readings)}

    first = readings[0]["pressure_hpa"]
    last = readings[-1]["pressure_hpa"]
    change = round(last - first, 2)

    if change < -3:
        trend = "falling_rapidly"
    elif change < -1:
        trend = "falling"
    elif change > 3:
        trend = "rising_rapidly"
    elif change > 1:
        trend = "rising"
    else:
        trend = "steady"

    return {"trend": trend, "change_hpa": change, "readings": len(readings)}


def get_pressure_trends() -> dict[str, Any]:
    """Get 3h, 6h, 12h pressure trends."""
    return {
        "3_hour": get_pressure_trend(3),
        "6_hour": get_pressure_trend(6),
        "12_hour": get_pressure_trend(12),
    }


def generate_forecast() -> dict[str, Any]:
    """Generate a simple forecast based on pattern rules."""
    pressure = get_pressure_trends()
    averages = get_all_moving_averages()

    # Get latest observation
    latest = query(
        "SELECT * FROM observations ORDER BY observed_at DESC LIMIT 1"
    )

    conditions: list[str] = []
    confidence = 30  # Base confidence

    p3 = pressure["3_hour"]
    p6 = pressure["6_hour"]

    # Count data points for confidence
    data_count = query(
        "SELECT COUNT(*) as cnt FROM observations WHERE observed_at >= ?",
        ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),),
    )
    if data_count and data_count[0]["cnt"] > 0:
        cnt = data_count[0]["cnt"]
        if cnt > 50:
            confidence += 20
        elif cnt > 20:
            confidence += 10

    # Rule: Rapid pressure drop -> storm
    if p3["trend"] == "falling_rapidly":
        conditions.append("Storm likely within 6-12 hours")
        confidence += 15
    elif p3["trend"] == "falling":
        conditions.append("Weather deteriorating, rain possible")
        confidence += 10

    # Rule: Pressure rising + clearing
    if p6["trend"] in ("rising", "rising_rapidly"):
        conditions.append("Fair weather approaching")
        confidence += 10

    # Rule: Steady pressure
    if p3["trend"] == "steady" and p6["trend"] == "steady":
        conditions.append("Conditions likely to persist")
        confidence += 15

    # Check cloud types for additional info
    if latest:
        cloud = latest[0].get("cloud_type")
        if cloud == "cumulonimbus":
            conditions.append("Thunderstorm activity possible")
            confidence += 5
        elif cloud == "clear":
            conditions.append("Clear skies observed")
            confidence += 5

    if not conditions:
        conditions.append("Insufficient data for detailed forecast")

    confidence = min(confidence, 95)

    now = datetime.now(timezone.utc)
    forecast = {
        "generated_at": now.isoformat(),
        "valid_from": now.isoformat(),
        "valid_to": (now + timedelta(hours=24)).isoformat(),
        "summary": "; ".join(conditions),
        "confidence_pct": confidence,
        "pressure_trends": pressure,
        "moving_averages": averages,
    }

    # Store forecast
    execute(
        """INSERT INTO forecasts
           (generated_at, valid_from, valid_to, summary, confidence_pct, method)
           VALUES (?, ?, ?, ?, ?, 'pattern_match')""",
        (
            forecast["generated_at"],
            forecast["valid_from"],
            forecast["valid_to"],
            forecast["summary"],
            forecast["confidence_pct"],
        ),
    )

    return forecast


def get_seasonal_normals() -> list[dict]:
    """Calculate seasonal normals from historical data grouped by month."""
    return query(
        """SELECT
            CAST(strftime('%m', observed_at) AS INTEGER) as month,
            ROUND(AVG(temperature_c), 1) as avg_temp_c,
            ROUND(MIN(temperature_c), 1) as min_temp_c,
            ROUND(MAX(temperature_c), 1) as max_temp_c,
            ROUND(AVG(humidity_pct), 1) as avg_humidity_pct,
            ROUND(AVG(pressure_hpa), 1) as avg_pressure_hpa,
            ROUND(SUM(rainfall_mm), 1) as total_rainfall_mm,
            COUNT(*) as observation_count
           FROM observations
           WHERE temperature_c IS NOT NULL
           GROUP BY strftime('%m', observed_at)
           ORDER BY month"""
    )
