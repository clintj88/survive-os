"""Lab results router — record results, alerts, and trends."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query

router = APIRouter(prefix="/api/results", tags=["results"])


class ResultCreate(BaseModel):
    order_id: int
    test_id: int
    value: str = ""
    numeric_value: float | None = None
    units: str = ""
    performed_by: str = ""
    notes: str = ""


def _interpret(numeric_value: float | None, test: dict) -> str:
    """Auto-calculate interpretation from reference ranges."""
    if numeric_value is None:
        return ""
    crit_low = test.get("critical_low")
    crit_high = test.get("critical_high")
    ref_min = test.get("ref_range_min")
    ref_max = test.get("ref_range_max")
    if crit_low is not None and numeric_value < crit_low:
        return "critical_low"
    if crit_high is not None and numeric_value > crit_high:
        return "critical_high"
    if ref_min is not None and numeric_value < ref_min:
        return "abnormal"
    if ref_max is not None and numeric_value > ref_max:
        return "abnormal"
    return "normal"


@router.post("", status_code=201)
def create_result(body: ResultCreate, _user: str = Depends(require_medical_role)) -> dict:
    order_rows = query("SELECT * FROM lab_orders WHERE id = ?", (body.order_id,))
    if not order_rows:
        raise HTTPException(status_code=404, detail="Order not found")
    test_rows = query("SELECT * FROM test_catalog WHERE id = ?", (body.test_id,))
    if not test_rows:
        raise HTTPException(status_code=404, detail="Test not found")

    interpretation = _interpret(body.numeric_value, test_rows[0])
    units = body.units or test_rows[0].get("units", "")

    row_id = execute(
        """INSERT INTO lab_results
           (order_id, test_id, value, numeric_value, units, interpretation,
            performed_by, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.order_id, body.test_id, body.value, body.numeric_value,
         units, interpretation, body.performed_by or _user, body.notes),
    )

    # Auto-complete the order
    execute(
        "UPDATE lab_orders SET status = 'completed', updated_at = datetime('now') WHERE id = ?",
        (body.order_id,),
    )

    return query("SELECT * FROM lab_results WHERE id = ?", (row_id,))[0]


@router.get("/alerts")
def get_alerts(
    patient_id: str | None = None,
    _user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = """SELECT lr.*, lo.patient_id, tc.name AS test_name
             FROM lab_results lr
             JOIN lab_orders lo ON lo.id = lr.order_id
             JOIN test_catalog tc ON tc.id = lr.test_id
             WHERE lr.interpretation IN ('abnormal', 'critical_low', 'critical_high')"""
    params: list = []
    if patient_id:
        sql += " AND lo.patient_id = ?"
        params.append(patient_id)
    sql += " ORDER BY lr.result_date DESC"
    return query(sql, tuple(params))


@router.get("/trends/{patient_id}/{test_id}")
def get_trends(
    patient_id: str, test_id: int, _user: str = Depends(require_medical_role),
) -> list[dict]:
    return query(
        """SELECT lr.numeric_value, lr.result_date, lr.interpretation, lr.units
           FROM lab_results lr
           JOIN lab_orders lo ON lo.id = lr.order_id
           WHERE lo.patient_id = ? AND lr.test_id = ?
           ORDER BY lr.result_date ASC""",
        (patient_id, test_id),
    )


@router.get("/patient/{patient_id}")
def get_patient_results(
    patient_id: str,
    test_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _user: str = Depends(require_medical_role),
) -> list[dict]:
    sql = """SELECT lr.*, lo.patient_id, lo.priority, tc.name AS test_name
             FROM lab_results lr
             JOIN lab_orders lo ON lo.id = lr.order_id
             JOIN test_catalog tc ON tc.id = lr.test_id
             WHERE lo.patient_id = ?"""
    params: list = [patient_id]
    if test_id is not None:
        sql += " AND lr.test_id = ?"
        params.append(test_id)
    if date_from:
        sql += " AND lr.result_date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND lr.result_date <= ?"
        params.append(date_to)
    sql += " ORDER BY lr.result_date DESC"
    return query(sql, tuple(params))
