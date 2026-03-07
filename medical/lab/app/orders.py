"""Lab orders router — CRUD with status workflow."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/orders", tags=["orders"])

VALID_TRANSITIONS: dict[str, list[str]] = {
    "ordered": ["collected", "cancelled"],
    "collected": ["processing", "cancelled"],
    "processing": ["completed", "cancelled"],
}


class OrderCreate(BaseModel):
    patient_id: str
    test_id: int | None = None
    panel_id: int | None = None
    ordered_by: str = ""
    priority: str = "routine"
    clinical_indication: str = ""


class OrderStatusUpdate(BaseModel):
    status: str


@router.get("")
def list_orders(
    patient_id: str | None = None,
    status: str | None = None,
    _user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = "SELECT * FROM lab_orders WHERE 1=1"
    params: list = []
    if patient_id:
        sql += " AND patient_id = ?"
        params.append(patient_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY ordered_at DESC"
    return query(sql, tuple(params))


@router.get("/{order_id}")
def get_order(order_id: int, _user: str = Depends(require_medical_role)) -> dict:
    rows = query("SELECT * FROM lab_orders WHERE id = ?", (order_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Order not found")
    return rows[0]


@router.post("", status_code=201)
def create_order(body: OrderCreate, _user: str = Depends(require_medical_role)) -> dict | list[dict]:
    if not body.test_id and not body.panel_id:
        raise HTTPException(status_code=400, detail="test_id or panel_id required")

    ordered_by = body.ordered_by or _user

    # If panel, create individual orders for each test in the panel
    if body.panel_id:
        panel_rows = query("SELECT * FROM lab_panels WHERE id = ?", (body.panel_id,))
        if not panel_rows:
            raise HTTPException(status_code=404, detail="Panel not found")
        panel_tests = query(
            "SELECT test_id FROM panel_tests WHERE panel_id = ? ORDER BY sort_order",
            (body.panel_id,),
        )
        if not panel_tests:
            raise HTTPException(status_code=400, detail="Panel has no tests")
        created = []
        for pt in panel_tests:
            oid = execute(
                """INSERT INTO lab_orders
                   (patient_id, test_id, panel_id, ordered_by, priority, clinical_indication)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (body.patient_id, pt["test_id"], body.panel_id,
                 ordered_by, body.priority, body.clinical_indication),
            )
            created.append(query("SELECT * FROM lab_orders WHERE id = ?", (oid,))[0])
        return created

    # Single test order
    if body.test_id:
        test_rows = query("SELECT * FROM test_catalog WHERE id = ?", (body.test_id,))
        if not test_rows:
            raise HTTPException(status_code=404, detail="Test not found")
    row_id = execute(
        """INSERT INTO lab_orders
           (patient_id, test_id, ordered_by, priority, clinical_indication)
           VALUES (?, ?, ?, ?, ?)""",
        (body.patient_id, body.test_id, ordered_by,
         body.priority, body.clinical_indication),
    )
    return query("SELECT * FROM lab_orders WHERE id = ?", (row_id,))[0]


@router.put("/{order_id}/status")
def update_order_status(
    order_id: int, body: OrderStatusUpdate, _user: str = Depends(require_medical_role),
) -> dict:
    rows = query("SELECT * FROM lab_orders WHERE id = ?", (order_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Order not found")
    current = rows[0]["status"]
    allowed = VALID_TRANSITIONS.get(current, [])
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{body.status}'",
        )
    extra = ""
    params: list = [body.status]
    if body.status == "collected":
        extra = ", collected_at = datetime('now')"
    params.append(order_id)
    execute(
        f"UPDATE lab_orders SET status = ?, updated_at = datetime('now'){extra} WHERE id = ?",
        tuple(params),
    )
    return query("SELECT * FROM lab_orders WHERE id = ?", (order_id,))[0]
