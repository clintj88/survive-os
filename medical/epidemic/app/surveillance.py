"""Syndromic surveillance routes."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .config import load_config
from .database import execute, query

router = APIRouter(prefix="/api/surveillance", tags=["surveillance"])

SYNDROME_CATEGORIES = [
    "respiratory",
    "gastrointestinal",
    "fever/febrile",
    "rash/dermatological",
    "neurological",
    "hemorrhagic",
    "other",
]

AGE_GROUPS = ["0-4", "5-14", "15-24", "25-44", "45-64", "65+"]


class SymptomReportCreate(BaseModel):
    date: str
    syndrome: str
    patient_id: Optional[str] = None
    age_group: str
    sex: str
    area: str = "default"
    notes: str = ""


class SymptomReportUpdate(BaseModel):
    syndrome: Optional[str] = None
    age_group: Optional[str] = None
    sex: Optional[str] = None
    area: Optional[str] = None
    notes: Optional[str] = None


@router.get("/syndromes")
def list_syndromes(_: str = Depends(require_medical_role)) -> list[str]:
    return SYNDROME_CATEGORIES


@router.get("/reports")
def list_reports(
    syndrome: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    conditions: list[str] = []
    params: list = []
    if syndrome:
        conditions.append("syndrome = ?")
        params.append(syndrome)
    if area:
        conditions.append("area = ?")
        params.append(area)
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"SELECT * FROM symptom_reports {where} ORDER BY date DESC",
        tuple(params),
    )


@router.get("/reports/{report_id}")
def get_report(report_id: int, _: str = Depends(require_medical_role)) -> dict:
    results = query("SELECT * FROM symptom_reports WHERE id = ?", (report_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Report not found")
    return results[0]


@router.post("/reports", status_code=201)
def create_report(
    report: SymptomReportCreate, _: str = Depends(require_medical_role)
) -> dict:
    if report.syndrome not in SYNDROME_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid syndrome. Must be one of: {SYNDROME_CATEGORIES}")
    if report.age_group not in AGE_GROUPS:
        raise HTTPException(status_code=400, detail=f"Invalid age group. Must be one of: {AGE_GROUPS}")
    if report.sex not in ("male", "female", "unknown"):
        raise HTTPException(status_code=400, detail="Sex must be male, female, or unknown")

    report_id = execute(
        """INSERT INTO symptom_reports (date, syndrome, patient_id, age_group, sex, area, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (report.date, report.syndrome, report.patient_id, report.age_group, report.sex, report.area, report.notes),
    )
    return get_report(report_id)


@router.put("/reports/{report_id}")
def update_report(
    report_id: int, report: SymptomReportUpdate, _: str = Depends(require_medical_role)
) -> dict:
    existing = query("SELECT id FROM symptom_reports WHERE id = ?", (report_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")

    updates: list[str] = []
    params: list = []
    for field in ("syndrome", "age_group", "sex", "area", "notes"):
        value = getattr(report, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(report_id)
    execute(f"UPDATE symptom_reports SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return get_report(report_id)


@router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: int, _: str = Depends(require_medical_role)) -> None:
    existing = query("SELECT id FROM symptom_reports WHERE id = ?", (report_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    execute("DELETE FROM symptom_reports WHERE id = ?", (report_id,))


@router.get("/counts")
def get_counts(
    syndrome: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("day"),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    """Get aggregated symptom counts grouped by day or week."""
    conditions: list[str] = []
    params: list = []
    if syndrome:
        conditions.append("syndrome = ?")
        params.append(syndrome)
    if area:
        conditions.append("area = ?")
        params.append(area)
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if group_by == "week":
        date_expr = "strftime('%Y-W%W', date)"
    else:
        date_expr = "date"

    return query(
        f"""SELECT {date_expr} as period, syndrome, COUNT(*) as count
            FROM symptom_reports {where}
            GROUP BY period, syndrome
            ORDER BY period""",
        tuple(params),
    )


@router.get("/baseline")
def get_baseline(
    syndrome: str = Query(...),
    area: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> dict:
    """Calculate rolling baseline for a syndrome."""
    config = load_config()
    weeks = config["surveillance"]["baseline_window_weeks"]
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(weeks=weeks)

    conditions = ["syndrome = ?", "date >= ?", "date <= ?"]
    params: list = [syndrome, start.isoformat(), end.isoformat()]
    if area:
        conditions.append("area = ?")
        params.append(area)

    where = " AND ".join(conditions)
    result = query(
        f"SELECT COUNT(*) as total FROM symptom_reports WHERE {where}",
        tuple(params),
    )
    total = result[0]["total"] if result else 0
    daily_baseline = total / (weeks * 7) if weeks > 0 else 0

    return {
        "syndrome": syndrome,
        "area": area or "all",
        "window_weeks": weeks,
        "total_in_window": total,
        "daily_baseline": round(daily_baseline, 2),
        "weekly_baseline": round(daily_baseline * 7, 2),
    }
