"""Threshold detection and alerting for epidemic surveillance."""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .config import load_config
from .database import execute, query

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
logger = logging.getLogger("epidemic.alerts")

_redis_client = None


def get_redis():
    """Get Redis client, creating if needed. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        config = load_config()
        _redis_client = redis.from_url(config["redis"]["url"])
        _redis_client.ping()
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable, alerts will not be published")
        return None


RECOMMENDATIONS = {
    "respiratory": "Increase ventilation, distribute masks, isolate symptomatic individuals",
    "gastrointestinal": "Check water sources, enforce hand hygiene, isolate food preparation areas",
    "fever/febrile": "Monitor for secondary symptoms, prepare isolation areas, check for vector breeding sites",
    "rash/dermatological": "Isolate affected individuals, check for common exposures, collect samples if possible",
    "neurological": "Seek specialist consultation, check for environmental toxins, monitor closely",
    "hemorrhagic": "Strict isolation protocols, full PPE required, notify regional health authority",
    "other": "Investigate common exposures, monitor for pattern development",
}


def _classify_alert_level(multiplier: float, thresholds: dict) -> Optional[str]:
    """Classify alert level based on multiplier and thresholds."""
    if multiplier >= thresholds["critical"]:
        return "critical"
    if multiplier >= thresholds["warning"]:
        return "warning"
    if multiplier >= thresholds["watch"]:
        return "watch"
    return None


@router.get("")
def list_alerts(
    active_only: bool = Query(False),
    syndrome: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if active_only:
        conditions.append("acknowledged = 0")
    if syndrome:
        conditions.append("syndrome = ?")
        params.append(syndrome)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(f"SELECT * FROM alerts {where} ORDER BY created_at DESC", tuple(params))


@router.get("/{alert_id}")
def get_alert(alert_id: int, _: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Alert not found")
    return results[0]


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, _: str = Depends(require_medical_role)) -> dict:
    existing = query("SELECT id FROM alerts WHERE id = ?", (alert_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Alert not found")
    execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    return get_alert(alert_id)


@router.post("/check")
def check_thresholds(
    area: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    """Run threshold check against baselines and generate alerts."""
    config = load_config()
    thresholds = config["surveillance"]["alert_thresholds"]
    weeks = config["surveillance"]["baseline_window_weeks"]

    today = datetime.now(timezone.utc).date()
    baseline_start = today - timedelta(weeks=weeks)

    area_condition = "AND area = ?" if area else ""
    area_params: tuple = (area,) if area else ()

    syndromes = query(
        f"SELECT DISTINCT syndrome FROM symptom_reports WHERE 1=1 {area_condition}",
        area_params,
    )

    new_alerts: list[dict] = []
    for row in syndromes:
        syndrome = row["syndrome"]

        # Current day count
        params_today = (today.isoformat(), syndrome) + area_params
        current = query(
            f"""SELECT COUNT(*) as count FROM symptom_reports
                WHERE date = ? AND syndrome = ? {area_condition}""",
            params_today,
        )
        current_count = current[0]["count"] if current else 0

        # Baseline daily average
        params_baseline = (baseline_start.isoformat(), today.isoformat(), syndrome) + area_params
        baseline = query(
            f"""SELECT COUNT(*) as total FROM symptom_reports
                WHERE date >= ? AND date < ? AND syndrome = ? {area_condition}""",
            params_baseline,
        )
        total = baseline[0]["total"] if baseline else 0
        daily_avg = total / (weeks * 7) if weeks > 0 else 0

        if daily_avg == 0:
            continue

        multiplier = current_count / daily_avg
        level = _classify_alert_level(multiplier, thresholds)
        if level is None:
            continue

        recommendation = RECOMMENDATIONS.get(syndrome, RECOMMENDATIONS["other"])
        alert_id = execute(
            """INSERT INTO alerts (syndrome, level, count, baseline, multiplier, area, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (syndrome, level, current_count, round(daily_avg, 2), round(multiplier, 2),
             area or "all", recommendation),
        )
        alert = get_alert(alert_id)
        new_alerts.append(alert)

        # Publish to Redis
        _publish_alert(alert)

    return new_alerts


def _publish_alert(alert: dict) -> None:
    """Publish alert to Redis channels."""
    r = get_redis()
    if r is None:
        return
    try:
        msg = json.dumps(alert, default=str)
        r.publish("medical.epidemic-alert", msg)
        r.publish("comms.alerts", msg)
    except Exception:
        logger.warning("Failed to publish alert to Redis")
