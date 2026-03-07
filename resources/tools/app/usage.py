"""Usage tracking and wear prediction API routes."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from .database import query

router = APIRouter(prefix="/api/usage", tags=["usage"])

# Average useful life in checkout-days by category
CATEGORY_LIFESPAN: dict[str, int] = {
    "hand_tools": 3650,
    "power_tools": 1825,
    "garden": 2190,
    "mechanical": 2555,
    "kitchen": 2920,
    "medical": 1460,
    "measuring": 3650,
    "safety": 1095,
}


@router.get("/stats/{tool_id}")
def tool_usage_stats(tool_id: int) -> dict:
    """Get usage statistics for a specific tool."""
    rows = query(
        """SELECT COUNT(*) as total_checkouts,
                  SUM(CASE WHEN actual_return_date IS NOT NULL
                      THEN CAST(julianday(actual_return_date) - julianday(checkout_date) AS INTEGER)
                      ELSE CAST(julianday('now') - julianday(checkout_date) AS INTEGER)
                  END) as total_days_used,
                  MIN(checkout_date) as first_used,
                  MAX(checkout_date) as last_used
           FROM checkouts WHERE tool_id = ?""",
        (tool_id,),
    )
    stats = rows[0] if rows else {"total_checkouts": 0, "total_days_used": 0}
    stats["total_days_used"] = stats["total_days_used"] or 0
    return stats


@router.get("/wear/{tool_id}")
def wear_prediction(tool_id: int) -> dict:
    """Predict remaining useful life based on usage rate and category."""
    tools = query("SELECT * FROM tools WHERE id = ?", (tool_id,))
    if not tools:
        return {"error": "Tool not found"}

    tool = tools[0]
    stats = tool_usage_stats(tool_id)

    lifespan = CATEGORY_LIFESPAN.get(tool["category"], 2555)
    used = stats["total_days_used"] or 0
    remaining = max(0, lifespan - used)
    wear_pct = min(100.0, round((used / lifespan) * 100, 1))

    # Estimate replacement date based on usage rate
    replacement_date = None
    if stats["total_checkouts"] and stats["first_used"] and remaining > 0:
        first = date.fromisoformat(stats["first_used"][:10])
        elapsed = (date.today() - first).days or 1
        daily_rate = used / elapsed
        if daily_rate > 0:
            days_left = int(remaining / daily_rate)
            replacement_date = (date.today() + timedelta(days=days_left)).isoformat()

    return {
        "tool_id": tool_id,
        "tool_name": tool["name"],
        "category": tool["category"],
        "condition": tool["condition"],
        "total_days_used": used,
        "expected_lifespan_days": lifespan,
        "remaining_life_days": remaining,
        "wear_percentage": wear_pct,
        "estimated_replacement_date": replacement_date,
    }


@router.get("/most-used")
def most_used(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    """Report of most-used tools by checkout count."""
    return query(
        """SELECT t.id, t.name, t.category, t.condition,
                  COUNT(c.id) as checkout_count,
                  SUM(CASE WHEN c.actual_return_date IS NOT NULL
                      THEN CAST(julianday(c.actual_return_date) - julianday(c.checkout_date) AS INTEGER)
                      ELSE CAST(julianday('now') - julianday(c.checkout_date) AS INTEGER)
                  END) as total_days_used
           FROM tools t
           JOIN checkouts c ON t.id = c.tool_id
           GROUP BY t.id
           ORDER BY checkout_count DESC
           LIMIT ?""",
        (limit,),
    )


@router.get("/replacement-alerts")
def replacement_alerts() -> list[dict]:
    """Tools that may need replacement soon (>80% wear)."""
    tools = query("SELECT * FROM tools WHERE status != 'retired'")
    alerts = []
    for tool in tools:
        pred = wear_prediction(tool["id"])
        if isinstance(pred, dict) and pred.get("wear_percentage", 0) >= 80:
            alerts.append(pred)
    return sorted(alerts, key=lambda x: x["wear_percentage"], reverse=True)
