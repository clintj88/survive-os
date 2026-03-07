"""Tests for the sensor integration API."""

import pytest
from fastapi.testclient import TestClient

from agriculture.sensors.app.database import init_db, set_db_path
from agriculture.sensors.app.frost import FrostMonitor
from agriculture.sensors.app.nodes import touch_node
from agriculture.sensors.app.queries import export_csv, query_readings


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "test_sensors.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Disable Redis connections during tests
    monkeypatch.setattr("agriculture.sensors.app.ingestion.HAS_REDIS", False)
    monkeypatch.setattr("agriculture.sensors.app.frost.HAS_REDIS", False)
    monkeypatch.setattr("agriculture.sensors.app.feeds.HAS_REDIS", False)

    from agriculture.sensors.app import main as main_mod
    test_config = main_mod.config.copy()
    test_config["database"] = {"path": str(tmp_path / "client_test.db")}
    monkeypatch.setattr(main_mod, "config", test_config)

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        yield c


# --- Health ---

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# --- Node CRUD ---

def test_create_node(client):
    resp = client.post("/api/nodes", json={
        "node_id": "esp32-001",
        "name": "Field A Soil",
        "location": "field-a",
        "type": "soil",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["node_id"] == "esp32-001"
    assert data["name"] == "Field A Soil"
    assert data["type"] == "soil"


def test_create_duplicate_node(client):
    client.post("/api/nodes", json={"node_id": "esp32-dup", "name": "Dup"})
    resp = client.post("/api/nodes", json={"node_id": "esp32-dup", "name": "Dup2"})
    assert resp.status_code == 409


def test_list_nodes(client):
    client.post("/api/nodes", json={"node_id": "n1", "name": "Node 1"})
    client.post("/api/nodes", json={"node_id": "n2", "name": "Node 2"})
    resp = client.get("/api/nodes")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_node(client):
    client.post("/api/nodes", json={"node_id": "n1", "name": "Node 1"})
    resp = client.get("/api/nodes/n1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Node 1"


def test_get_node_not_found(client):
    resp = client.get("/api/nodes/nonexistent")
    assert resp.status_code == 404


def test_update_node(client):
    client.post("/api/nodes", json={"node_id": "n1", "name": "Old"})
    resp = client.put("/api/nodes/n1", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_node(client):
    client.post("/api/nodes", json={"node_id": "n1", "name": "Node"})
    resp = client.delete("/api/nodes/n1")
    assert resp.status_code == 204
    resp = client.get("/api/nodes/n1")
    assert resp.status_code == 404


# --- Node auto-discovery ---

def test_touch_node_creates():
    touch_node("auto-001", battery_level=95.0, firmware_version="1.0.0")
    from agriculture.sensors.app.nodes import get_node
    node = get_node("auto-001")
    assert node is not None
    assert node["status"] == "online"
    assert node["battery_level"] == 95.0


# --- Sensor data ingestion ---

def test_store_and_query_soil():
    from agriculture.sensors.app.database import execute
    touch_node("soil-001")
    execute(
        """INSERT INTO soil_readings (node_id, moisture_pct, depth_cm, temperature_c, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("soil-001", 42.5, 10.0, 18.3, "2026-03-07T10:00:00"),
    )
    results = query_readings("soil", node_id="soil-001")
    assert len(results) == 1
    assert results[0]["moisture_pct"] == 42.5


def test_store_and_query_weather():
    from agriculture.sensors.app.database import execute
    touch_node("wx-001")
    execute(
        """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct, pressure_hpa, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("wx-001", 5.2, 85.0, 1013.25, "2026-03-07T10:00:00"),
    )
    results = query_readings("weather", node_id="wx-001")
    assert len(results) == 1
    assert results[0]["temperature_c"] == 5.2


def test_store_and_query_rain():
    from agriculture.sensors.app.database import execute
    touch_node("rain-001")
    execute(
        """INSERT INTO rain_readings (node_id, rainfall_mm, period_minutes, timestamp)
           VALUES (?, ?, ?, ?)""",
        ("rain-001", 3.5, 60, "2026-03-07T10:00:00"),
    )
    results = query_readings("rain", node_id="rain-001")
    assert len(results) == 1
    assert results[0]["rainfall_mm"] == 3.5


# --- Aggregation ---

def test_hourly_aggregation():
    from agriculture.sensors.app.database import execute
    touch_node("wx-agg")
    for i in range(3):
        execute(
            """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct, pressure_hpa, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            ("wx-agg", 10.0 + i, 80.0, 1013.0, f"2026-03-07T10:{i:02d}:00"),
        )
    results = query_readings("weather", node_id="wx-agg", aggregation="hourly")
    assert len(results) == 1
    assert results[0]["reading_count"] == 3
    assert results[0]["avg_temperature_c"] == pytest.approx(11.0)


# --- CSV export ---

def test_csv_export():
    from agriculture.sensors.app.database import execute
    touch_node("csv-node")
    execute(
        """INSERT INTO soil_readings (node_id, moisture_pct, depth_cm, temperature_c, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("csv-node", 55.0, 20.0, 15.0, "2026-03-07T12:00:00"),
    )
    csv_data = export_csv("soil", node_id="csv-node")
    assert "moisture_pct" in csv_data
    assert "55.0" in csv_data


def test_csv_export_api(client):
    resp = client.get("/api/readings/soil/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"


# --- Frost alerts ---

@pytest.mark.asyncio
async def test_frost_detection():
    from agriculture.sensors.app.database import execute
    from agriculture.sensors.app.config import load_config

    cfg = load_config()
    monitor = FrostMonitor(cfg)

    touch_node("frost-001")
    # Add prior readings for trend
    execute(
        """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct, pressure_hpa, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("frost-001", 5.0, 90.0, 1013.0, "2026-03-07T01:00:00"),
    )
    execute(
        """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct, pressure_hpa, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("frost-001", 3.0, 92.0, 1013.0, "2026-03-07T02:00:00"),
    )
    execute(
        """INSERT INTO weather_readings (node_id, temperature_c, humidity_pct, pressure_hpa, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        ("frost-001", 1.5, 95.0, 1013.0, "2026-03-07T03:00:00"),
    )

    alert = await monitor.check_reading({
        "node_id": "frost-001",
        "temperature_c": 1.5,
        "timestamp": "2026-03-07T03:00:00",
    })
    assert alert is not None
    assert alert["temperature_c"] == 1.5
    assert alert["trend"] == "falling"

    alerts = monitor.get_recent_alerts()
    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_no_frost_above_threshold():
    from agriculture.sensors.app.config import load_config

    cfg = load_config()
    monitor = FrostMonitor(cfg)

    touch_node("warm-001")
    alert = await monitor.check_reading({
        "node_id": "warm-001",
        "temperature_c": 15.0,
    })
    assert alert is None


# --- Dashboard ---

def test_dashboard(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "weather" in data
    assert "soil" in data
    assert "rain" in data


# --- API validation ---

def test_invalid_sensor_type(client):
    resp = client.get("/api/readings/invalid")
    assert resp.status_code == 400


def test_readings_api(client):
    resp = client.get("/api/readings/weather")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_frost_alerts_api(client):
    resp = client.get("/api/alerts/frost")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
