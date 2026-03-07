"""API routes for the alerts module."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .broadcaster import broadcast_alert
from .config import load_config
from .database import execute, query

router = APIRouter(prefix="/api")
config = load_config()


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str  # info, warning, critical, emergency
    author: str


class AlertResolve(BaseModel):
    resolved_by: str


class AlertAck(BaseModel):
    user_id: str


VALID_SEVERITIES = {"info", "warning", "critical", "emergency"}


# --- Alerts ---

@router.get("/alerts")
def list_alerts(
    active: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
) -> list[dict]:
    conditions = []
    params: list = []

    if active is not None:
        conditions.append("active = ?")
        params.append(1 if active else 0)
    if severity is not None:
        if severity not in VALID_SEVERITIES:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        conditions.append("severity = ?")
        params.append(severity)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    return query(
        f"""SELECT a.id, a.title, a.message, a.severity, a.author,
                   a.active, a.created_at, a.resolved_at, a.resolved_by,
                   COUNT(ack.id) as ack_count
            FROM alerts a
            LEFT JOIN alert_acknowledgments ack ON ack.alert_id = a.id
            {where}
            GROUP BY a.id
            ORDER BY a.created_at DESC""",
        tuple(params),
    )


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int) -> dict:
    results = query(
        """SELECT id, title, message, severity, author, active,
                  created_at, resolved_at, resolved_by
           FROM alerts WHERE id = ?""",
        (alert_id,),
    )
    if not results:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = results[0]
    alert["acknowledgments"] = query(
        "SELECT user_id, acknowledged_at FROM alert_acknowledgments WHERE alert_id = ?",
        (alert_id,),
    )
    alert["broadcasts"] = query(
        "SELECT channel, status, sent_at, error FROM alert_broadcast_log WHERE alert_id = ?",
        (alert_id,),
    )
    return alert


@router.post("/alerts", status_code=201)
def create_alert(alert: AlertCreate) -> dict:
    if alert.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {alert.severity}")

    alert_id = execute(
        "INSERT INTO alerts (title, message, severity, author) VALUES (?, ?, ?, ?)",
        (alert.title, alert.message, alert.severity, alert.author),
    )

    alert_data = query("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    alert_dict = dict(alert_data[0])

    # Broadcast to all channels
    channels = config.get("broadcast_channels", ["comms.alerts"])
    broadcast_results = broadcast_alert(alert_dict, channels)

    # Log broadcast results
    for entry in broadcast_results:
        execute(
            """INSERT INTO alert_broadcast_log (alert_id, channel, status, error)
               VALUES (?, ?, ?, ?)""",
            (alert_id, entry["channel"], entry["status"], entry.get("error")),
        )

    return get_alert(alert_id)


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, resolve: AlertResolve) -> dict:
    existing = query("SELECT id, active FROM alerts WHERE id = ?", (alert_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not existing[0]["active"]:
        raise HTTPException(status_code=400, detail="Alert already resolved")

    execute(
        "UPDATE alerts SET active = 0, resolved_at = ?, resolved_by = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), resolve.resolved_by, alert_id),
    )
    return get_alert(alert_id)


@router.post("/alerts/{alert_id}/ack", status_code=201)
def acknowledge_alert(alert_id: int, ack: AlertAck) -> dict:
    if not query("SELECT id FROM alerts WHERE id = ?", (alert_id,)):
        raise HTTPException(status_code=404, detail="Alert not found")

    # Check for duplicate ack
    existing_ack = query(
        "SELECT id FROM alert_acknowledgments WHERE alert_id = ? AND user_id = ?",
        (alert_id, ack.user_id),
    )
    if existing_ack:
        raise HTTPException(status_code=409, detail="Already acknowledged")

    execute(
        "INSERT INTO alert_acknowledgments (alert_id, user_id) VALUES (?, ?)",
        (alert_id, ack.user_id),
    )
    return {"alert_id": alert_id, "user_id": ack.user_id, "status": "acknowledged"}


@router.get("/alerts/{alert_id}/acks")
def list_acknowledgments(alert_id: int) -> list[dict]:
    if not query("SELECT id FROM alerts WHERE id = ?", (alert_id,)):
        raise HTTPException(status_code=404, detail="Alert not found")
    return query(
        "SELECT user_id, acknowledged_at FROM alert_acknowledgments WHERE alert_id = ?",
        (alert_id,),
    )
