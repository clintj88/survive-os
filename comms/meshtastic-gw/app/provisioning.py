"""Radio provisioning API endpoints."""

import logging
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .database import execute, query

logger = logging.getLogger("meshtastic-gw.provisioning")

router = APIRouter(prefix="/api/provisioning", tags=["provisioning"])


class RadioAssignment(BaseModel):
    node_id: str
    user: str


class ChannelConfig(BaseModel):
    index: int
    name: str
    psk: str = ""


_gateway: Any = None
_lldap_url: str = "http://localhost:17170"


def init_provisioning(gateway: Any, lldap_url: str) -> None:
    """Initialize provisioning with gateway and LLDAP URL."""
    global _gateway, _lldap_url
    _gateway = gateway
    _lldap_url = lldap_url


@router.get("/radios")
def list_radios() -> list[dict[str, Any]]:
    """List all known radios from the database."""
    return query(
        """SELECT id, node_id, long_name, short_name, hw_model,
                  assigned_user, connection_type, battery_level, snr,
                  last_seen, latitude, longitude, altitude
           FROM radios ORDER BY last_seen DESC"""
    )


@router.get("/radios/scan")
async def scan_radios() -> list[dict[str, Any]]:
    """Scan for available radios and update the database."""
    if not _gateway:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    nodes = _gateway.get_node_list()
    for node in nodes:
        existing = query("SELECT id FROM radios WHERE node_id = ?", (node["node_id"],))
        if existing:
            execute(
                """UPDATE radios SET long_name=?, short_name=?, hw_model=?,
                          battery_level=?, snr=?, last_seen=?,
                          latitude=?, longitude=?, altitude=?
                   WHERE node_id=?""",
                (node["long_name"], node["short_name"], node["hw_model"],
                 node["battery_level"], node["snr"], node["last_seen"],
                 node["latitude"], node["longitude"], node["altitude"],
                 node["node_id"]),
            )
        else:
            execute(
                """INSERT INTO radios (node_id, long_name, short_name, hw_model,
                          battery_level, snr, last_seen, latitude, longitude, altitude)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (node["node_id"], node["long_name"], node["short_name"],
                 node["hw_model"], node["battery_level"], node["snr"],
                 node["last_seen"], node["latitude"], node["longitude"],
                 node["altitude"]),
            )
    return list_radios()


@router.post("/radios/assign")
def assign_radio(assignment: RadioAssignment) -> dict[str, Any]:
    """Assign a radio to a user."""
    existing = query("SELECT id FROM radios WHERE node_id = ?", (assignment.node_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Radio not found")

    execute(
        "UPDATE radios SET assigned_user = ? WHERE node_id = ?",
        (assignment.user, assignment.node_id),
    )
    rows = query("SELECT * FROM radios WHERE node_id = ?", (assignment.node_id,))
    return rows[0]


@router.get("/users")
async def list_users() -> list[dict[str, Any]]:
    """List users from LLDAP directory."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{_lldap_url}/api/graphql",
                json={"query": "{ users { id displayName } }"},
            )
            if resp.status_code == 200:
                data = resp.json()
                users = data.get("data", {}).get("users", [])
                return [{"id": u["id"], "name": u["displayName"]} for u in users]
    except Exception:
        logger.warning("Could not reach LLDAP at %s", _lldap_url)
    return []


@router.get("/channels")
def list_channels() -> list[dict[str, Any]]:
    """List configured channels."""
    if _gateway and _gateway.connected:
        return _gateway.get_channels()
    return query("SELECT id, name, role, psk FROM channels ORDER BY id")


@router.get("/topology")
def get_topology() -> dict[str, Any]:
    """Get mesh network topology data."""
    nodes = query(
        """SELECT node_id, long_name, short_name, snr, battery_level,
                  last_seen, latitude, longitude
           FROM radios ORDER BY last_seen DESC"""
    )
    return {"nodes": nodes}
