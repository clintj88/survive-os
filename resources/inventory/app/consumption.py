"""Consumption tracking for inventory items."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .audit import log_action
from .database import execute, query

router = APIRouter(prefix="/api/consumption", tags=["consumption"])


class ConsumptionCreate(BaseModel):
    item_id: int
    quantity_consumed: float
    consumed_by: str = ""
    purpose: str = ""
    date: Optional[str] = None


@router.post("", status_code=201)
def record_consumption(event: ConsumptionCreate) -> dict:
    items = query("SELECT id, name, quantity FROM items WHERE id = ?", (event.item_id,))
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")

    item = items[0]
    if event.quantity_consumed <= 0:
        raise HTTPException(status_code=400, detail="Quantity consumed must be positive")

    new_quantity = max(0, item["quantity"] - event.quantity_consumed)
    execute("UPDATE items SET quantity = ?, updated_at = datetime('now') WHERE id = ?",
            (new_quantity, event.item_id))

    date_val = event.date or None
    params = (event.item_id, event.quantity_consumed, event.consumed_by, event.purpose)
    if date_val:
        event_id = execute(
            """INSERT INTO consumption_events (item_id, quantity_consumed, date, consumed_by, purpose)
               VALUES (?, ?, ?, ?, ?)""",
            (event.item_id, event.quantity_consumed, date_val, event.consumed_by, event.purpose),
        )
    else:
        event_id = execute(
            """INSERT INTO consumption_events (item_id, quantity_consumed, consumed_by, purpose)
               VALUES (?, ?, ?, ?)""",
            params,
        )

    log_action(
        event.item_id, "consume", event.consumed_by,
        -event.quantity_consumed, item["quantity"], new_quantity,
        f"Consumed for: {event.purpose}",
    )

    return {
        "id": event_id,
        "item_id": event.item_id,
        "item_name": item["name"],
        "quantity_consumed": event.quantity_consumed,
        "previous_quantity": item["quantity"],
        "new_quantity": new_quantity,
    }


@router.get("/history/{item_id}")
def consumption_history(
    item_id: int,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict]:
    items = query("SELECT id FROM items WHERE id = ?", (item_id,))
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")

    return query(
        """SELECT * FROM consumption_events
           WHERE item_id = ? ORDER BY date DESC LIMIT ?""",
        (item_id, limit),
    )


@router.get("/rate/{item_id}")
def consumption_rate(item_id: int) -> dict:
    items = query("SELECT id, name, quantity, unit FROM items WHERE id = ?", (item_id,))
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")

    item = items[0]

    # Calculate daily average from last 30 days
    events = query(
        """SELECT SUM(quantity_consumed) as total, COUNT(*) as count,
                  MIN(date) as first_date, MAX(date) as last_date
           FROM consumption_events
           WHERE item_id = ? AND date >= datetime('now', '-30 days')""",
        (item_id,),
    )

    total_consumed = events[0]["total"] or 0
    event_count = events[0]["count"] or 0

    # Calculate rate based on 30-day window
    daily_rate = total_consumed / 30.0 if total_consumed > 0 else 0
    weekly_rate = daily_rate * 7

    # Days of supply projection
    days_of_supply = item["quantity"] / daily_rate if daily_rate > 0 else None

    return {
        "item_id": item_id,
        "item_name": item["name"],
        "current_quantity": item["quantity"],
        "unit": item["unit"],
        "daily_rate": round(daily_rate, 2),
        "weekly_rate": round(weekly_rate, 2),
        "total_consumed_30d": round(total_consumed, 2),
        "events_30d": event_count,
        "days_of_supply": round(days_of_supply, 1) if days_of_supply is not None else None,
    }
