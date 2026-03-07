"""Tests for the Weather Station API."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _past_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Observations CRUD ---

def test_create_observation(client: TestClient) -> None:
    resp = client.post("/api/observations", json={
        "observed_at": _now_iso(),
        "observer": "tester",
        "temperature_c": 22.5,
        "humidity_pct": 65.0,
        "pressure_hpa": 1013.25,
        "wind_speed_kph": 15.0,
        "wind_direction": "NW",
        "cloud_type": "cumulus",
        "precipitation": "none",
        "visibility": "good",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["temperature_c"] == 22.5
    assert data["observer"] == "tester"
    assert data["source"] == "manual"


def test_create_observation_minimal(client: TestClient) -> None:
    resp = client.post("/api/observations", json={
        "observed_at": _now_iso(),
    })
    assert resp.status_code == 201


def test_create_observation_invalid_cloud(client: TestClient) -> None:
    resp = client.post("/api/observations", json={
        "observed_at": _now_iso(),
        "cloud_type": "tornado_cloud",
    })
    assert resp.status_code == 422


def test_create_observation_invalid_precipitation(client: TestClient) -> None:
    resp = client.post("/api/observations", json={
        "observed_at": _now_iso(),
        "precipitation": "extreme",
    })
    assert resp.status_code == 422


def test_list_observations(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 20.0})
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 25.0})
    resp = client.get("/api/observations")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_observations_filter_source(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 20.0})
    resp = client.get("/api/observations?source=manual")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    resp = client.get("/api/observations?source=sensor")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_observation(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 18.0})
    resp = client.get("/api/observations/1")
    assert resp.status_code == 200
    assert resp.json()["temperature_c"] == 18.0


def test_get_observation_not_found(client: TestClient) -> None:
    resp = client.get("/api/observations/999")
    assert resp.status_code == 404


def test_latest_observation(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _past_iso(2), "temperature_c": 15.0})
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 20.0})
    resp = client.get("/api/observations/latest")
    assert resp.status_code == 200
    assert resp.json()["temperature_c"] == 20.0


def test_latest_observation_empty(client: TestClient) -> None:
    resp = client.get("/api/observations/latest")
    assert resp.status_code == 404


def test_update_observation(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso(), "temperature_c": 20.0})
    resp = client.put("/api/observations/1", json={"temperature_c": 22.0})
    assert resp.status_code == 200
    assert resp.json()["temperature_c"] == 22.0


def test_update_observation_not_found(client: TestClient) -> None:
    resp = client.put("/api/observations/999", json={"temperature_c": 22.0})
    assert resp.status_code == 404


def test_update_observation_no_fields(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso()})
    resp = client.put("/api/observations/1", json={})
    assert resp.status_code == 400


def test_delete_observation(client: TestClient) -> None:
    client.post("/api/observations", json={"observed_at": _now_iso()})
    resp = client.delete("/api/observations/1")
    assert resp.status_code == 204
    resp = client.get("/api/observations/1")
    assert resp.status_code == 404


def test_delete_observation_not_found(client: TestClient) -> None:
    resp = client.delete("/api/observations/999")
    assert resp.status_code == 404


# --- Sensor Ingestion ---

def test_sensor_ingest() -> None:
    from app.sensors import ingest_sensor_data
    obs_id = ingest_sensor_data({
        "temperature_c": 21.0,
        "humidity_pct": 55.0,
        "pressure_hpa": 1010.0,
        "sensor_id": "test-sensor",
    })
    assert obs_id is not None
    rows = query("SELECT * FROM observations WHERE id = ?", (obs_id,))
    assert rows[0]["source"] == "sensor"
    assert rows[0]["temperature_c"] == 21.0


def test_sensor_ingest_outlier() -> None:
    from app.sensors import ingest_sensor_data
    obs_id = ingest_sensor_data({"temperature_c": 999.0})
    assert obs_id is None


def test_sensor_validate() -> None:
    from app.sensors import validate_sensor_reading
    cleaned = validate_sensor_reading({
        "temperature_c": 25.0,
        "humidity_pct": 150.0,
        "pressure_hpa": 1013.0,
    })
    assert "temperature_c" in cleaned
    assert "humidity_pct" not in cleaned
    assert "pressure_hpa" in cleaned


# --- Analysis ---

def test_forecast_no_data(client: TestClient) -> None:
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "confidence_pct" in data


def test_forecast_with_data(client: TestClient) -> None:
    now = datetime.now(timezone.utc)
    for i in range(5):
        t = (now - timedelta(hours=i)).isoformat()
        execute(
            """INSERT INTO observations (observed_at, observer, source, temperature_c, pressure_hpa)
               VALUES (?, 'test', 'manual', ?, ?)""",
            (t, 20.0 - i, 1013.0 - i * 2),
        )
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert data["confidence_pct"] >= 30


def test_pressure_trends(client: TestClient) -> None:
    resp = client.get("/api/analysis/pressure")
    assert resp.status_code == 200
    data = resp.json()
    assert "3_hour" in data
    assert "6_hour" in data
    assert "12_hour" in data


def test_moving_averages(client: TestClient) -> None:
    resp = client.get("/api/analysis/averages")
    assert resp.status_code == 200
    data = resp.json()
    assert "temperature_c" in data


def test_seasonal_normals(client: TestClient) -> None:
    resp = client.get("/api/analysis/seasonal-normals")
    assert resp.status_code == 200


# --- Planting ---

def test_frost_dates_empty(client: TestClient) -> None:
    resp = client.get("/api/planting/frost-dates")
    assert resp.status_code == 200
    assert resp.json() == []


def test_record_frost_date(client: TestClient) -> None:
    resp = client.post("/api/planting/frost-dates?year=2026&frost_type=last_spring&frost_date=2026-04-20")
    assert resp.status_code == 201
    data = resp.json()
    assert data["year"] == 2026
    assert data["frost_type"] == "last_spring"


def test_growing_season(client: TestClient) -> None:
    client.post("/api/planting/frost-dates?year=2026&frost_type=last_spring&frost_date=2026-04-15")
    client.post("/api/planting/frost-dates?year=2026&frost_type=first_fall&frost_date=2026-10-15")
    resp = client.get("/api/planting/growing-season?year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["growing_season_days"] == 183


def test_planting_windows(client: TestClient) -> None:
    resp = client.get("/api/planting/windows")
    assert resp.status_code == 200
    windows = resp.json()
    assert len(windows) == 4


def test_advisories(client: TestClient) -> None:
    resp = client.post("/api/planting/advisories?message=Frost+risk+tonight&advisory_type=frost_warning")
    assert resp.status_code == 201
    resp = client.get("/api/planting/advisories")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- Storms ---

def test_active_storms_empty(client: TestClient) -> None:
    resp = client.get("/api/storms/active")
    assert resp.status_code == 200
    assert resp.json() == []


def test_storm_history_empty(client: TestClient) -> None:
    resp = client.get("/api/storms/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_storm_check_no_data(client: TestClient) -> None:
    resp = client.post("/api/storms/check")
    assert resp.status_code == 200
    assert resp.json() == []


def test_storm_detection_pressure_drop(client: TestClient) -> None:
    now = datetime.now(timezone.utc)
    execute(
        """INSERT INTO observations (observed_at, observer, source, pressure_hpa)
           VALUES (?, 'test', 'sensor', ?)""",
        ((now - timedelta(hours=2)).isoformat(), 1020.0),
    )
    execute(
        """INSERT INTO observations (observed_at, observer, source, pressure_hpa)
           VALUES (?, 'test', 'sensor', ?)""",
        (now.isoformat(), 1014.0),
    )
    resp = client.post("/api/storms/check")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "pressure_drop"
    assert events[0]["severity"] in ("warning", "emergency")

    resp = client.get("/api/storms/active")
    assert len(resp.json()) >= 1


def test_storm_detection_high_wind(client: TestClient) -> None:
    execute(
        """INSERT INTO observations (observed_at, observer, source, wind_speed_kph)
           VALUES (?, 'test', 'sensor', ?)""",
        (_now_iso(), 80.0),
    )
    resp = client.post("/api/storms/check")
    events = resp.json()
    wind_events = [e for e in events if e["event_type"] == "high_wind"]
    assert len(wind_events) == 1


def test_end_storm(client: TestClient) -> None:
    from app.storms import create_storm_event
    eid = create_storm_event({
        "event_type": "test",
        "severity": "watch",
        "description": "Test storm",
    })
    resp = client.post(f"/api/storms/{eid}/end?total_precip_mm=25.0")
    assert resp.status_code == 200
    storms = query("SELECT * FROM storm_events WHERE id = ?", (eid,))
    assert storms[0]["active"] == 0
    assert storms[0]["total_precipitation_mm"] == 25.0


# --- Trends ---

def _seed_trend_data() -> None:
    """Insert a year of monthly observations for trend testing."""
    for month in range(1, 13):
        for day in (1, 15):
            dt = f"2025-{month:02d}-{day:02d}T12:00:00"
            execute(
                """INSERT INTO observations
                   (observed_at, observer, source, temperature_c, humidity_pct, pressure_hpa, rainfall_mm)
                   VALUES (?, 'test', 'manual', ?, ?, ?, ?)""",
                (dt, 5.0 + month * 2, 50.0 + month, 1013.0, month * 3.0),
            )


def test_monthly_averages(client: TestClient) -> None:
    _seed_trend_data()
    resp = client.get("/api/trends/monthly?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 12


def test_seasonal_averages(client: TestClient) -> None:
    _seed_trend_data()
    resp = client.get("/api/trends/seasonal?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4


def test_annual_summary(client: TestClient) -> None:
    _seed_trend_data()
    resp = client.get("/api/trends/annual?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["year"] == "2025"


def test_year_over_year(client: TestClient) -> None:
    _seed_trend_data()
    # Add 2024 data for comparison
    execute(
        """INSERT INTO observations
           (observed_at, observer, source, temperature_c, humidity_pct, rainfall_mm)
           VALUES (?, 'test', 'manual', ?, ?, ?)""",
        ("2024-06-15T12:00:00", 22.0, 60.0, 5.0),
    )
    resp = client.get("/api/trends/year-over-year?month=6")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_growing_degree_days(client: TestClient) -> None:
    _seed_trend_data()
    resp = client.get("/api/trends/gdd?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == 2025
    assert data["total_gdd"] > 0
    assert data["days_with_data"] == 24


def test_rainfall_by_season(client: TestClient) -> None:
    _seed_trend_data()
    resp = client.get("/api/trends/rainfall?year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
