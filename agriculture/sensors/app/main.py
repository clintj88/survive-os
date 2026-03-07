"""Sensor Integration API - SURVIVE OS Agriculture Module."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .database import init_db, set_db_path
from .feeds import DataFeed
from .frost import FrostMonitor
from .ingestion import SensorIngestion
from .nodes import (
    NodeCreate, NodeUpdate,
    check_offline_nodes, create_node, delete_node, get_node, list_nodes, update_node,
)
from .queries import export_csv, query_readings

logger = logging.getLogger("survive-sensors")
config = load_config()
VERSION = config["version"]

ingestion = SensorIngestion(config)
frost_monitor = FrostMonitor(config)
data_feed = DataFeed(config)


async def on_reading(sensor_type: str, data: dict) -> None:
    """Callback for each ingested reading - check frost and publish feeds."""
    if sensor_type == "weather":
        await frost_monitor.check_reading(data)
        await data_feed.publish_weather_observation(data)


async def _node_health_loop() -> None:
    """Periodically check for offline nodes."""
    timeout = config["node_timeout"]["minutes"]
    while True:
        try:
            await asyncio.sleep(60)
            check_offline_nodes(timeout)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Node health check error")


async def _prune_loop() -> None:
    """Daily pruning of old data."""
    while True:
        try:
            await asyncio.sleep(86400)
            count = ingestion.prune_old_data()
            if count:
                logger.info("Pruned %d old readings", count)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Data pruning error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_db_path(config["database"]["path"])
    init_db()

    ingestion.set_reading_callback(on_reading)
    await ingestion.connect()
    await ingestion.start()
    await frost_monitor.connect()
    await data_feed.connect()

    health_task = asyncio.create_task(_node_health_loop())
    prune_task = asyncio.create_task(_prune_loop())

    yield

    health_task.cancel()
    prune_task.cancel()
    await ingestion.stop()
    await frost_monitor.stop()
    await data_feed.stop()


app = FastAPI(title="SURVIVE OS Sensor Integration", version=VERSION, lifespan=lifespan)


# --- Health ---

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": VERSION}


# --- Node CRUD ---

@app.get("/api/nodes")
def api_list_nodes() -> list[dict]:
    return list_nodes()


@app.get("/api/nodes/{node_id}")
def api_get_node(node_id: str) -> dict:
    node = get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.post("/api/nodes", status_code=201)
def api_create_node(node: NodeCreate) -> dict:
    existing = get_node(node.node_id)
    if existing:
        raise HTTPException(status_code=409, detail="Node already exists")
    return create_node(node)


@app.put("/api/nodes/{node_id}")
def api_update_node(node_id: str, node: NodeUpdate) -> dict:
    result = update_node(node_id, node)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@app.delete("/api/nodes/{node_id}", status_code=204)
def api_delete_node(node_id: str) -> None:
    if not delete_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")


# --- Dashboard ---

@app.get("/api/dashboard")
def api_dashboard() -> dict:
    return data_feed.get_latest_readings()


# --- Sensor Data Queries ---

@app.get("/api/readings/{sensor_type}")
def api_readings(
    sensor_type: str,
    node_id: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    aggregation: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000),
) -> list[dict]:
    if sensor_type not in ("soil", "weather", "rain"):
        raise HTTPException(status_code=400, detail="Invalid sensor type")
    return query_readings(sensor_type, node_id, start, end, aggregation, limit)


@app.get("/api/readings/{sensor_type}/csv")
def api_csv_export(
    sensor_type: str,
    node_id: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
) -> Response:
    if sensor_type not in ("soil", "weather", "rain"):
        raise HTTPException(status_code=400, detail="Invalid sensor type")
    csv_data = export_csv(sensor_type, node_id, start, end)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={sensor_type}_readings.csv"},
    )


# --- Frost Alerts ---

@app.get("/api/alerts/frost")
def api_frost_alerts(limit: int = Query(50, le=500)) -> list[dict]:
    return frost_monitor.get_recent_alerts(limit)


# --- Static files ---

_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
