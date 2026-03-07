"""Ham Radio Integration API - SURVIVE OS Comms Module."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config
from .database import execute, init_db, query, set_db_path
from .frequencies import router as freq_router
from .scheduler import router as sched_router
from .pat_client import PatClient
from .js8call import JS8CallClient

logger = logging.getLogger("survive-ham-radio")

config = load_config()
VERSION = config["version"]

pat_client = PatClient(config["pat"]["binary"], config["pat"]["mycall"])
js8_client = JS8CallClient(config["js8call"]["host"], config["js8call"]["port"])


def _try_publish(channel: str, message: str) -> None:
    """Publish event to Redis, silently fail if unavailable."""
    try:
        import redis
        r = redis.from_url(config["redis"]["url"])
        r.publish(channel, message)
    except Exception:
        logger.debug("Redis publish failed (offline mode)")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()
    # Seed frequencies if table is empty
    from .database import query as db_query
    if not db_query("SELECT id FROM frequencies LIMIT 1"):
        from seed.frequencies import seed_frequencies
        seed_frequencies()
        logger.info("Seeded frequency database")
    yield


app = FastAPI(title="SURVIVE OS Ham Radio", version=VERSION, lifespan=lifespan)
app.include_router(freq_router)
app.include_router(sched_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "js8call_connected": js8_client.is_connected(),
    }


# --- Winlink / Pat endpoints ---

class WinlinkCompose(BaseModel):
    to: str
    subject: str
    body: str


@app.get("/api/winlink/messages")
def list_winlink_messages(direction: Optional[str] = None) -> list[dict]:
    if direction:
        return query(
            "SELECT * FROM winlink_messages WHERE direction = ? ORDER BY created_at DESC",
            (direction,),
        )
    return query("SELECT * FROM winlink_messages ORDER BY created_at DESC")


@app.get("/api/winlink/messages/{msg_id}")
def get_winlink_message(msg_id: int) -> dict:
    results = query("SELECT * FROM winlink_messages WHERE id = ?", (msg_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Message not found")
    return results[0]


@app.post("/api/winlink/compose", status_code=201)
def compose_winlink(msg: WinlinkCompose) -> dict:
    mid = execute(
        """INSERT INTO winlink_messages (direction, from_addr, to_addr, subject, body, status)
           VALUES ('outbound', ?, ?, ?, ?, 'queued')""",
        (config["pat"]["mycall"], msg.to, msg.subject, msg.body),
    )
    _try_publish("comms.ham-radio", f"winlink:composed:{mid}")
    return get_winlink_message(mid)


@app.post("/api/winlink/send")
def send_winlink() -> dict:
    success = pat_client.send()
    if success:
        execute(
            "UPDATE winlink_messages SET status = 'sent', sent_at = datetime('now') WHERE status = 'queued'"
        )
        _try_publish("comms.ham-radio", "winlink:sent")
    return {"success": success}


@app.post("/api/winlink/receive")
def receive_winlink() -> dict:
    messages = pat_client.list_inbox()
    imported = 0
    for msg in messages:
        msg_id = msg.get("id", msg.get("message_id", ""))
        existing = query("SELECT id FROM winlink_messages WHERE message_id = ?", (msg_id,))
        if not existing:
            execute(
                """INSERT INTO winlink_messages (message_id, direction, from_addr, to_addr, subject, body, status)
                   VALUES (?, 'inbound', ?, ?, ?, ?, 'received')""",
                (msg_id, msg.get("from", ""), msg.get("to", ""),
                 msg.get("subject", ""), msg.get("body", "")),
            )
            imported += 1
    if imported:
        _try_publish("comms.ham-radio", f"winlink:received:{imported}")
    return {"imported": imported, "total": len(messages)}


# --- JS8Call endpoints ---

class JS8SendMessage(BaseModel):
    to_call: str
    message: str


@app.get("/api/js8call/status")
def js8call_status() -> dict:
    connected = js8_client.is_connected()
    station = js8_client.get_station_info() if connected else {}
    return {"connected": connected, "station": station}


@app.post("/api/js8call/send")
def js8call_send(msg: JS8SendMessage) -> dict:
    success = js8_client.send_message(msg.to_call, msg.message)
    if success:
        execute(
            """INSERT INTO js8call_messages (direction, from_call, to_call, message)
               VALUES ('outbound', ?, ?, ?)""",
            (config["pat"]["mycall"], msg.to_call, msg.message),
        )
        _try_publish("comms.ham-radio", f"js8call:sent:{msg.to_call}")
    return {"success": success}


@app.get("/api/js8call/activity")
def js8call_activity() -> dict:
    calls = js8_client.get_call_activity()
    band = js8_client.get_band_activity()
    return {"calls": calls, "band": band}


@app.get("/api/js8call/messages")
def list_js8call_messages() -> list[dict]:
    return query("SELECT * FROM js8call_messages ORDER BY created_at DESC")


# Mount static files last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
