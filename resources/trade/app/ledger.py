"""Double-entry bookkeeping for trade/barter records."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

router = APIRouter(prefix="/api/trades", tags=["ledger"])


class TradeItemCreate(BaseModel):
    side: str  # 'give' or 'receive'
    item_description: str
    quantity: float
    unit: str
    value_in_labor_hours: float = 0


class TradeCreate(BaseModel):
    party_a: str
    party_b: str
    description: str = ""
    items: list[TradeItemCreate]


class TradeStatusUpdate(BaseModel):
    status: str  # pending, completed, disputed, cancelled


@router.get("")
def list_trades(
    status: Optional[str] = None,
    party: Optional[str] = None,
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if status:
        conditions.append("t.status = ?")
        params.append(status)
    if party:
        conditions.append("(t.party_a = ? OR t.party_b = ?)")
        params.extend([party, party])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    trades = query(
        f"""SELECT t.id, t.date, t.party_a, t.party_b, t.description,
                   t.status, t.created_at, t.updated_at
            FROM trades t {where}
            ORDER BY t.date DESC""",
        tuple(params),
    )
    for trade in trades:
        trade["items"] = query(
            """SELECT id, side, item_description, quantity, unit, value_in_labor_hours
               FROM trade_items WHERE trade_id = ? ORDER BY side, id""",
            (trade["id"],),
        )
    return trades


@router.get("/{trade_id}")
def get_trade(trade_id: int) -> dict:
    results = query(
        """SELECT id, date, party_a, party_b, description, status,
                  created_at, updated_at
           FROM trades WHERE id = ?""",
        (trade_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Trade not found")
    trade = results[0]
    trade["items"] = query(
        """SELECT id, side, item_description, quantity, unit, value_in_labor_hours
           FROM trade_items WHERE trade_id = ? ORDER BY side, id""",
        (trade_id,),
    )
    return trade


@router.post("", status_code=201)
def create_trade(trade: TradeCreate) -> dict:
    if not trade.items:
        raise HTTPException(status_code=400, detail="Trade must have at least one item")

    has_give = any(i.side == "give" for i in trade.items)
    has_receive = any(i.side == "receive" for i in trade.items)
    if not has_give or not has_receive:
        raise HTTPException(
            status_code=400,
            detail="Trade must have items on both give and receive sides",
        )

    for item in trade.items:
        if item.side not in ("give", "receive"):
            raise HTTPException(status_code=400, detail=f"Invalid side: {item.side}")

    trade_id = execute(
        """INSERT INTO trades (party_a, party_b, description)
           VALUES (?, ?, ?)""",
        (trade.party_a, trade.party_b, trade.description),
    )

    for item in trade.items:
        execute(
            """INSERT INTO trade_items (trade_id, side, item_description, quantity, unit, value_in_labor_hours)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (trade_id, item.side, item.item_description, item.quantity, item.unit, item.value_in_labor_hours),
        )

    return get_trade(trade_id)


@router.patch("/{trade_id}/status")
def update_trade_status(trade_id: int, update: TradeStatusUpdate) -> dict:
    existing = query("SELECT id FROM trades WHERE id = ?", (trade_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Trade not found")
    if update.status not in ("pending", "completed", "disputed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")

    now = datetime.now(timezone.utc).isoformat()
    execute(
        "UPDATE trades SET status = ?, updated_at = ? WHERE id = ?",
        (update.status, now, trade_id),
    )
    return get_trade(trade_id)


@router.get("/{trade_id}/validate")
def validate_trade(trade_id: int) -> dict:
    """Check if a trade's give and receive sides balance in labor hours."""
    existing = query("SELECT id FROM trades WHERE id = ?", (trade_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Trade not found")

    items = query(
        "SELECT side, value_in_labor_hours FROM trade_items WHERE trade_id = ?",
        (trade_id,),
    )
    give_total = sum(i["value_in_labor_hours"] for i in items if i["side"] == "give")
    receive_total = sum(i["value_in_labor_hours"] for i in items if i["side"] == "receive")
    balanced = abs(give_total - receive_total) < 0.01

    return {
        "trade_id": trade_id,
        "give_total_hours": give_total,
        "receive_total_hours": receive_total,
        "balanced": balanced,
    }
