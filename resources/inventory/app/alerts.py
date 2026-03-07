"""Stock level alerts for inventory items."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .config import load_config
from .database import execute, query

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
logger = logging.getLogger("survive-inventory")


class ThresholdCreate(BaseModel):
    item_id: Optional[int] = None
    category: Optional[str] = None
    min_level: float


def _publish_alert(alert: dict) -> None:
    """Publish alert to Redis channel. Degrades gracefully if Redis unavailable."""
    try:
        import redis
        config = load_config()
        r = redis.from_url(config["redis"]["url"])
        r.publish("resources.inventory-alerts", json.dumps(alert))
    except Exception as e:
        logger.warning(f"Could not publish alert to Redis: {e}")


def _get_min_level(item_id: int, category: str) -> Optional[float]:
    """Get minimum stock level for an item (item-specific threshold takes priority)."""
    item_threshold = query(
        "SELECT min_level FROM alert_thresholds WHERE item_id = ?", (item_id,)
    )
    if item_threshold:
        return item_threshold[0]["min_level"]

    cat_threshold = query(
        "SELECT min_level FROM alert_thresholds WHERE category = ? AND item_id IS NULL",
        (category,),
    )
    if cat_threshold:
        return cat_threshold[0]["min_level"]

    config = load_config()
    return config["alerts"]["default_min_stock"]


def _get_alert_level(quantity: float, min_level: float) -> Optional[str]:
    if quantity <= 0:
        return "depleted"
    if quantity < min_level:
        return "critical"
    if quantity < min_level * 2:
        return "low"
    return None


def check_and_publish_alerts(item_id: int) -> None:
    """Check stock level for an item and publish alert if needed."""
    items = query("SELECT id, name, category, quantity, unit FROM items WHERE id = ?", (item_id,))
    if not items:
        return

    item = items[0]
    min_level = _get_min_level(item_id, item["category"])
    if min_level is None:
        return

    alert_level = _get_alert_level(item["quantity"], min_level)
    if alert_level:
        alert = {
            "item_id": item["id"],
            "item_name": item["name"],
            "category": item["category"],
            "quantity": item["quantity"],
            "unit": item["unit"],
            "min_level": min_level,
            "alert_level": alert_level,
        }
        _publish_alert(alert)


@router.post("/thresholds", status_code=201)
def create_threshold(threshold: ThresholdCreate) -> dict:
    if threshold.item_id is None and threshold.category is None:
        raise HTTPException(status_code=400, detail="Must specify item_id or category")
    if threshold.min_level < 0:
        raise HTTPException(status_code=400, detail="min_level must be non-negative")

    if threshold.item_id is not None:
        items = query("SELECT id FROM items WHERE id = ?", (threshold.item_id,))
        if not items:
            raise HTTPException(status_code=404, detail="Item not found")
        # Upsert: delete existing item-specific threshold
        execute("DELETE FROM alert_thresholds WHERE item_id = ?", (threshold.item_id,))

    if threshold.category is not None and threshold.item_id is None:
        # Upsert: delete existing category threshold
        execute("DELETE FROM alert_thresholds WHERE category = ? AND item_id IS NULL",
                (threshold.category,))

    tid = execute(
        "INSERT INTO alert_thresholds (item_id, category, min_level) VALUES (?, ?, ?)",
        (threshold.item_id, threshold.category, threshold.min_level),
    )
    return {"id": tid, **threshold.model_dump()}


@router.get("/thresholds")
def list_thresholds() -> list[dict]:
    return query("SELECT * FROM alert_thresholds ORDER BY id")


@router.delete("/thresholds/{threshold_id}")
def delete_threshold(threshold_id: int) -> dict:
    existing = query("SELECT id FROM alert_thresholds WHERE id = ?", (threshold_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Threshold not found")
    execute("DELETE FROM alert_thresholds WHERE id = ?", (threshold_id,))
    return {"detail": "Threshold deleted"}


@router.get("")
def get_active_alerts() -> list[dict]:
    """Get all items that are below their minimum stock level."""
    items = query("SELECT id, name, category, quantity, unit FROM items")
    alerts = []

    for item in items:
        min_level = _get_min_level(item["id"], item["category"])
        if min_level is None:
            continue

        alert_level = _get_alert_level(item["quantity"], min_level)
        if alert_level:
            alerts.append({
                "item_id": item["id"],
                "item_name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "min_level": min_level,
                "alert_level": alert_level,
            })

    # Sort by severity: depleted > critical > low
    severity_order = {"depleted": 0, "critical": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["alert_level"], 3))
    return alerts
