"""Audit logging for inventory changes."""

from typing import Optional

from fastapi import APIRouter, Query

from .database import execute, query

router = APIRouter(prefix="/api/audit", tags=["audit"])


def log_action(
    item_id: Optional[int],
    action: str,
    performed_by: str = "",
    quantity_change: Optional[float] = None,
    previous_quantity: Optional[float] = None,
    new_quantity: Optional[float] = None,
    notes: str = "",
) -> int:
    return execute(
        """INSERT INTO audit_log (item_id, action, quantity_change, previous_quantity,
           new_quantity, performed_by, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (item_id, action, quantity_change, previous_quantity, new_quantity, performed_by, notes),
    )


@router.get("")
def list_audit_entries(
    item_id: Optional[int] = Query(None),
    performed_by: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []

    if item_id is not None:
        conditions.append("a.item_id = ?")
        params.append(item_id)
    if performed_by:
        conditions.append("a.performed_by = ?")
        params.append(performed_by)
    if date_from:
        conditions.append("a.timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("a.timestamp <= ?")
        params.append(date_to)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    return query(
        f"""SELECT a.*, i.name as item_name
            FROM audit_log a
            LEFT JOIN items i ON a.item_id = i.id
            {where}
            ORDER BY a.timestamp DESC
            LIMIT ? OFFSET ?""",
        tuple(params),
    )


@router.get("/report")
def audit_report(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
) -> dict:
    conditions: list[str] = []
    params: list = []

    if date_from:
        conditions.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("timestamp <= ?")
        params.append(date_to)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    by_action = query(
        f"SELECT action, COUNT(*) as count FROM audit_log {where} GROUP BY action",
        tuple(params),
    )
    by_user = query(
        f"""SELECT performed_by, COUNT(*) as count FROM audit_log
            {where} GROUP BY performed_by ORDER BY count DESC""",
        tuple(params),
    )
    total = query(f"SELECT COUNT(*) as count FROM audit_log {where}", tuple(params))

    return {
        "total_entries": total[0]["count"] if total else 0,
        "by_action": by_action,
        "by_user": by_user,
    }
