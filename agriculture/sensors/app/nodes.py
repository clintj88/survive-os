"""Sensor node registry and health monitoring."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic import BaseModel

from .database import execute, query


class NodeCreate(BaseModel):
    node_id: str
    name: str = ""
    location: str = ""
    type: str = "unknown"
    firmware_version: str = ""


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    firmware_version: Optional[str] = None


def list_nodes() -> list[dict]:
    return query("SELECT * FROM nodes ORDER BY name, node_id")


def get_node(node_id: str) -> Optional[dict]:
    results = query("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
    return results[0] if results else None


def create_node(node: NodeCreate) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    execute(
        """INSERT INTO nodes (node_id, name, location, type, firmware_version,
           status, last_seen, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'online', ?, ?, ?)""",
        (node.node_id, node.name, node.location, node.type,
         node.firmware_version, now, now, now),
    )
    return get_node(node.node_id)  # type: ignore


def update_node(node_id: str, node: NodeUpdate) -> Optional[dict]:
    updates: list[str] = []
    params: list = []
    for field in ("name", "location", "type", "firmware_version"):
        value = getattr(node, field)
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        return get_node(node_id)
    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(node_id)
    execute(f"UPDATE nodes SET {', '.join(updates)} WHERE node_id = ?", tuple(params))
    return get_node(node_id)


def delete_node(node_id: str) -> bool:
    existing = get_node(node_id)
    if not existing:
        return False
    execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
    return True


def touch_node(node_id: str, battery_level: Optional[float] = None,
               firmware_version: Optional[str] = None) -> None:
    """Update last_seen and status for a node, auto-register if unknown."""
    now = datetime.now(timezone.utc).isoformat()
    existing = get_node(node_id)
    if not existing:
        execute(
            """INSERT INTO nodes (node_id, name, location, type, status,
               last_seen, battery_level, firmware_version, created_at, updated_at)
               VALUES (?, ?, '', 'unknown', 'online', ?, ?, ?, ?, ?)""",
            (node_id, node_id, now, battery_level, firmware_version or "", now, now),
        )
    else:
        extras = ["last_seen = ?", "status = 'online'", "updated_at = ?"]
        params: list = [now, now]
        if battery_level is not None:
            extras.append("battery_level = ?")
            params.append(battery_level)
        if firmware_version:
            extras.append("firmware_version = ?")
            params.append(firmware_version)
        params.append(node_id)
        execute(f"UPDATE nodes SET {', '.join(extras)} WHERE node_id = ?", tuple(params))


def check_offline_nodes(timeout_minutes: int = 30) -> list[dict]:
    """Find nodes that haven't reported within the timeout period."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)).isoformat()
    # Mark stale nodes as offline
    execute(
        "UPDATE nodes SET status = 'offline' WHERE last_seen < ? AND status = 'online'",
        (cutoff,),
    )
    return query(
        "SELECT * FROM nodes WHERE status = 'offline' ORDER BY last_seen",
    )
