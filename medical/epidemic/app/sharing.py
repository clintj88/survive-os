"""Cross-community anonymized data sharing."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import require_medical_role
from .database import execute, query
from .alerts import get_redis

router = APIRouter(prefix="/api/sharing", tags=["sharing"])
logger = logging.getLogger("epidemic.sharing")


class IncomingCommunityData(BaseModel):
    community_id: str
    date: str
    syndrome: str
    age_group: str
    count: int


@router.get("/export")
def export_anonymized(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    """Export anonymized aggregate counts (no PII)."""
    conditions: list[str] = []
    params: list = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return query(
        f"""SELECT date, syndrome, age_group, COUNT(*) as count
            FROM symptom_reports {where}
            GROUP BY date, syndrome, age_group
            ORDER BY date""",
        tuple(params),
    )


@router.post("/broadcast")
def broadcast_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> dict:
    """Broadcast anonymized data via ham radio (Redis channel)."""
    data = export_anonymized(start_date, end_date, _)
    r = get_redis()
    if r is None:
        return {"status": "error", "message": "Redis unavailable"}

    try:
        msg = json.dumps({"type": "epidemic_syndromic_data", "data": data}, default=str)
        r.publish("comms.ham-radio", msg)
        return {"status": "sent", "records": len(data)}
    except Exception:
        logger.warning("Failed to broadcast data")
        return {"status": "error", "message": "Failed to publish"}


@router.post("/receive", status_code=201)
def receive_community_data(
    records: list[IncomingCommunityData],
    _: str = Depends(require_medical_role),
) -> dict:
    """Ingest anonymized data from another community."""
    count = 0
    for rec in records:
        execute(
            """INSERT INTO community_data (community_id, date, syndrome, age_group, count)
               VALUES (?, ?, ?, ?, ?)""",
            (rec.community_id, rec.date, rec.syndrome, rec.age_group, rec.count),
        )
        count += 1
    return {"status": "ok", "ingested": count}


@router.get("/communities")
def list_communities(_: str = Depends(require_medical_role)) -> list[dict]:
    """List communities we have received data from."""
    return query(
        """SELECT community_id, MIN(date) as first_date, MAX(date) as last_date,
                  SUM(count) as total_reports, COUNT(DISTINCT syndrome) as syndromes_tracked
           FROM community_data
           GROUP BY community_id
           ORDER BY last_date DESC"""
    )


@router.get("/comparison")
def compare_communities(
    syndrome: Optional[str] = Query(None),
    _: str = Depends(require_medical_role),
) -> list[dict]:
    """Compare syndromic data across communities."""
    condition = "WHERE syndrome = ?" if syndrome else ""
    params = (syndrome,) if syndrome else ()

    return query(
        f"""SELECT community_id, syndrome, date, SUM(count) as count
            FROM community_data {condition}
            GROUP BY community_id, syndrome, date
            ORDER BY date""",
        params,
    )
