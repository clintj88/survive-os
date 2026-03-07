"""Meshtastic Gateway API - SURVIVE OS Comms Module."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config
from .database import execute, init_db, query, set_db_path
from .gateway import MeshtasticGateway
from .provisioning import init_provisioning, router as provisioning_router
from .redis_bridge import RedisBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meshtastic-gw")

config = load_config()
VERSION = config["version"]

gateway = MeshtasticGateway(config)
redis_bridge = RedisBridge(config)


def on_mesh_message(msg: dict[str, Any]) -> None:
    """Forward mesh messages to Redis."""
    msg["source"] = "meshtastic-gw"
    asyncio.create_task(redis_bridge.publish(msg))


async def on_redis_message(msg: dict[str, Any]) -> None:
    """Forward Redis messages to the mesh."""
    text = msg.get("content", "")
    destination = msg.get("recipient", "^all")
    channel = msg.get("channel", 0)
    if text:
        await gateway.send_message(text, destination, channel)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    init_provisioning(gateway, config["lldap"]["url"])

    gateway.set_message_callback(on_mesh_message)
    await gateway.connect()

    redis_connected = await redis_bridge.connect()
    if redis_connected:
        redis_bridge.set_message_callback(on_redis_message)
        await redis_bridge.start_listener()

    reconnect_task = asyncio.create_task(gateway.auto_reconnect())

    yield

    reconnect_task.cancel()
    await gateway.disconnect()
    await redis_bridge.disconnect()


app = FastAPI(title="SURVIVE OS Meshtastic Gateway", version=VERSION, lifespan=lifespan)
app.include_router(provisioning_router)


class MessageSend(BaseModel):
    content: str
    recipient: str = "^all"
    channel: int = 0


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "radio_connected": gateway.connected,
    }


@app.get("/api/messages")
def list_messages(
    channel: Optional[int] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    if channel is not None:
        return query(
            """SELECT id, sender, recipient, content, timestamp, channel,
                      mesh_id, direction, ack
               FROM messages WHERE channel = ?
               ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
            (channel, limit, offset),
        )
    return query(
        """SELECT id, sender, recipient, content, timestamp, channel,
                  mesh_id, direction, ack
           FROM messages ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
        (limit, offset),
    )


@app.post("/api/messages", status_code=201)
async def send_message(msg: MessageSend) -> dict:
    sent = await gateway.send_message(msg.content, msg.recipient, msg.channel)
    if not sent:
        # Store locally even if radio is not connected
        execute(
            """INSERT INTO messages (sender, recipient, content, timestamp, channel, direction)
               VALUES ('local', ?, ?, ?, ?, 'tx')""",
            (msg.recipient, msg.content,
             datetime.now(timezone.utc).isoformat(), msg.channel),
        )

    await redis_bridge.publish({
        "source": "meshtastic-gw",
        "sender": "local",
        "recipient": msg.recipient,
        "content": msg.content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": msg.channel,
    })

    return {"sent": sent, "content": msg.content, "recipient": msg.recipient}


@app.get("/api/status")
def get_status() -> dict:
    return {
        "radio_connected": gateway.connected,
        "connection_type": config["radio"]["connection"],
        "serial_port": config["radio"]["serial_port"],
        "ble_address": config["radio"]["ble_address"],
        "message_count": query("SELECT COUNT(*) as count FROM messages")[0]["count"],
        "node_count": query("SELECT COUNT(*) as count FROM radios")[0]["count"],
    }


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
