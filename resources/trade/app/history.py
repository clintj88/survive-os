"""Trade history and balance tracking."""

from typing import Optional

from fastapi import APIRouter

from .database import query

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/person/{person}")
def person_history(
    person: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Full trade history for a person."""
    conditions = ["(t.party_a = ? OR t.party_b = ?)"]
    params: list = [person, person]
    if status:
        conditions.append("t.status = ?")
        params.append(status)
    params.append(limit)
    where = " AND ".join(conditions)
    trades = query(
        f"""SELECT t.id, t.date, t.party_a, t.party_b, t.description,
                   t.status, t.created_at
            FROM trades t
            WHERE {where}
            ORDER BY t.date DESC
            LIMIT ?""",
        tuple(params),
    )
    for trade in trades:
        trade["items"] = query(
            """SELECT id, side, item_description, quantity, unit, value_in_labor_hours
               FROM trade_items WHERE trade_id = ? ORDER BY side, id""",
            (trade["id"],),
        )
    return trades


@router.get("/balance/{party_a}/{party_b}")
def balance_between(party_a: str, party_b: str) -> dict:
    """Running balance between two parties in labor hours."""
    # Trades where party_a gave to party_b
    a_gave = query(
        """SELECT COALESCE(SUM(ti.value_in_labor_hours), 0) as total
           FROM trade_items ti
           JOIN trades t ON ti.trade_id = t.id
           WHERE t.status = 'completed'
             AND t.party_a = ? AND t.party_b = ?
             AND ti.side = 'give'""",
        (party_a, party_b),
    )
    # Trades where party_b gave to party_a
    b_gave = query(
        """SELECT COALESCE(SUM(ti.value_in_labor_hours), 0) as total
           FROM trade_items ti
           JOIN trades t ON ti.trade_id = t.id
           WHERE t.status = 'completed'
             AND t.party_a = ? AND t.party_b = ?
             AND ti.side = 'give'""",
        (party_b, party_a),
    )
    a_total = a_gave[0]["total"] if a_gave else 0
    b_total = b_gave[0]["total"] if b_gave else 0
    net = a_total - b_total

    return {
        "party_a": party_a,
        "party_b": party_b,
        "a_gave_hours": a_total,
        "b_gave_hours": b_total,
        "net_balance_hours": net,
        "summary": f"{party_a} owes {party_b} {abs(net):.2f} hours"
        if net > 0
        else f"{party_b} owes {party_a} {abs(net):.2f} hours"
        if net < 0
        else "Balanced",
    }


@router.get("/summary")
def trade_summary() -> dict:
    """Trade volume statistics."""
    total_trades = query("SELECT COUNT(*) as count FROM trades")
    completed = query("SELECT COUNT(*) as count FROM trades WHERE status = 'completed'")
    pending = query("SELECT COUNT(*) as count FROM trades WHERE status = 'pending'")
    disputed = query("SELECT COUNT(*) as count FROM trades WHERE status = 'disputed'")

    top_items = query(
        """SELECT item_description, SUM(quantity) as total_quantity, unit,
                  COUNT(*) as trade_count
           FROM trade_items
           JOIN trades t ON trade_items.trade_id = t.id
           WHERE t.status = 'completed'
           GROUP BY item_description, unit
           ORDER BY trade_count DESC
           LIMIT 10"""
    )

    top_traders = query(
        """SELECT person, COUNT(*) as trade_count,
                  SUM(total_hours) as total_hours
           FROM (
               SELECT party_a as person, id,
                      (SELECT COALESCE(SUM(value_in_labor_hours), 0)
                       FROM trade_items WHERE trade_id = trades.id) as total_hours
               FROM trades WHERE status = 'completed'
               UNION ALL
               SELECT party_b as person, id,
                      (SELECT COALESCE(SUM(value_in_labor_hours), 0)
                       FROM trade_items WHERE trade_id = trades.id) as total_hours
               FROM trades WHERE status = 'completed'
           ) sub
           GROUP BY person
           ORDER BY trade_count DESC
           LIMIT 10"""
    )

    return {
        "total_trades": total_trades[0]["count"],
        "completed": completed[0]["count"],
        "pending": pending[0]["count"],
        "disputed": disputed[0]["count"],
        "top_items": top_items,
        "top_traders": top_traders,
    }
