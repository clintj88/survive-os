"""Tests for the Energy & Fuel Tracking API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- Helpers ---

def _create_panel(client: TestClient, **overrides) -> dict:
    data = {"name": "Panel A", "rated_watts": 300, "location": "Roof South"}
    data.update(overrides)
    resp = client.post("/api/solar/panels", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_bank(client: TestClient, **overrides) -> dict:
    data = {"name": "Main Bank", "type": "lithium", "capacity_ah": 200, "voltage": 48}
    data.update(overrides)
    resp = client.post("/api/batteries/banks", json=data)
    assert resp.status_code == 201
    return resp.json()


def _create_generator(client: TestClient, **overrides) -> dict:
    data = {"name": "Honda EU2200i", "fuel_type": "gasoline", "rated_kw": 2.2}
    data.update(overrides)
    resp = client.post("/api/generators", json=data)
    assert resp.status_code == 201
    return resp.json()


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Solar ---

def test_create_and_list_panels(client: TestClient) -> None:
    _create_panel(client)
    _create_panel(client, name="Panel B", rated_watts=400)

    resp = client.get("/api/solar/panels")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_and_update_panel(client: TestClient) -> None:
    panel = _create_panel(client)
    resp = client.get(f"/api/solar/panels/{panel['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Panel A"

    resp = client.put(f"/api/solar/panels/{panel['id']}", json={"rated_watts": 350})
    assert resp.status_code == 200
    assert resp.json()["rated_watts"] == 350


def test_delete_panel(client: TestClient) -> None:
    panel = _create_panel(client)
    resp = client.delete(f"/api/solar/panels/{panel['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/solar/panels/{panel['id']}")
    assert resp.status_code == 404


def test_log_solar_output(client: TestClient) -> None:
    panel = _create_panel(client)
    resp = client.post("/api/solar/output", json={
        "panel_id": panel["id"],
        "watts_output": 250,
        "irradiance": 800,
    })
    assert resp.status_code == 201
    assert resp.json()["watts_output"] == 250

    resp = client.get(f"/api/solar/output/{panel['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_solar_output_nonexistent_panel(client: TestClient) -> None:
    resp = client.post("/api/solar/output", json={
        "panel_id": 999,
        "watts_output": 250,
    })
    assert resp.status_code == 404


def test_daily_production(client: TestClient) -> None:
    panel = _create_panel(client)
    client.post("/api/solar/output", json={
        "panel_id": panel["id"],
        "watts_output": 200,
        "timestamp": "2026-03-07 10:00:00",
    })
    client.post("/api/solar/output", json={
        "panel_id": panel["id"],
        "watts_output": 300,
        "timestamp": "2026-03-07 12:00:00",
    })

    resp = client.get("/api/solar/production/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["total_wh"] == 500


def test_panel_efficiency(client: TestClient) -> None:
    panel = _create_panel(client, rated_watts=300)
    client.post("/api/solar/output", json={
        "panel_id": panel["id"], "watts_output": 150,
    })
    client.post("/api/solar/output", json={
        "panel_id": panel["id"], "watts_output": 250,
    })

    resp = client.get("/api/solar/efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["avg_output_watts"] == 200.0
    assert round(data[0]["efficiency_percent"], 2) == 66.67


# --- Batteries ---

def test_create_and_list_banks(client: TestClient) -> None:
    _create_bank(client)
    _create_bank(client, name="Backup Bank", type="lead-acid", capacity_ah=100, voltage=24)

    resp = client.get("/api/batteries/banks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_and_update_bank(client: TestClient) -> None:
    bank = _create_bank(client)
    resp = client.get(f"/api/batteries/banks/{bank['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Main Bank"

    resp = client.put(f"/api/batteries/banks/{bank['id']}", json={"capacity_ah": 250})
    assert resp.status_code == 200
    assert resp.json()["capacity_ah"] == 250


def test_delete_bank(client: TestClient) -> None:
    bank = _create_bank(client)
    resp = client.delete(f"/api/batteries/banks/{bank['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/batteries/banks/{bank['id']}")
    assert resp.status_code == 404


def test_log_battery_state(client: TestClient) -> None:
    bank = _create_bank(client)
    resp = client.post("/api/batteries/state", json={
        "bank_id": bank["id"],
        "voltage": 51.2,
        "current_amps": 10.5,
        "soc_percent": 85,
        "temperature": 25.0,
    })
    assert resp.status_code == 201
    assert resp.json()["soc_percent"] == 85


def test_battery_state_history(client: TestClient) -> None:
    bank = _create_bank(client)
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 51.0, "soc_percent": 80,
    })
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 52.0, "soc_percent": 90,
    })

    resp = client.get(f"/api/batteries/state/{bank['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_latest_state(client: TestClient) -> None:
    bank = _create_bank(client)
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 50.0, "soc_percent": 70,
    })
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 52.0, "soc_percent": 95,
    })

    resp = client.get(f"/api/batteries/state/{bank['id']}/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["latest_state"]["soc_percent"] == 95
    assert data["capacity_wh"] == 200 * 48


def test_battery_cycles(client: TestClient) -> None:
    bank = _create_bank(client, type="lithium")
    # Simulate charge/discharge cycle
    for soc in [50, 60, 80, 95, 90, 70, 50, 60, 80]:
        client.post("/api/batteries/state", json={
            "bank_id": bank["id"], "voltage": 48.0, "soc_percent": soc,
        })

    resp = client.get(f"/api/batteries/cycles/{bank['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["estimated_cycles"] >= 1
    assert data["expected_max_cycles"] == 2000
    assert data["health_percent"] > 0


def test_low_battery_alerts(client: TestClient) -> None:
    bank = _create_bank(client)
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 44.0, "soc_percent": 15,
    })

    resp = client.get("/api/batteries/low-battery?threshold=20")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["soc_percent"] == 15


def test_no_low_battery_alerts(client: TestClient) -> None:
    bank = _create_bank(client)
    client.post("/api/batteries/state", json={
        "bank_id": bank["id"], "voltage": 52.0, "soc_percent": 90,
    })

    resp = client.get("/api/batteries/low-battery?threshold=20")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# --- Fuel ---

def test_add_and_list_fuel(client: TestClient) -> None:
    resp = client.post("/api/fuel/storage", json={
        "fuel_type": "diesel",
        "quantity": 200,
        "unit": "liters",
        "storage_location": "Tank 1",
    })
    assert resp.status_code == 201
    assert resp.json()["fuel_type"] == "diesel"

    resp = client.get("/api/fuel/storage")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_filter_fuel_by_type(client: TestClient) -> None:
    client.post("/api/fuel/storage", json={
        "fuel_type": "diesel", "quantity": 100, "unit": "liters",
    })
    client.post("/api/fuel/storage", json={
        "fuel_type": "gasoline", "quantity": 50, "unit": "liters",
    })

    resp = client.get("/api/fuel/storage?fuel_type=diesel")
    assert len(resp.json()) == 1


def test_delete_fuel_storage(client: TestClient) -> None:
    resp = client.post("/api/fuel/storage", json={
        "fuel_type": "propane", "quantity": 30, "unit": "kg",
    })
    entry_id = resp.json()["id"]

    resp = client.delete(f"/api/fuel/storage/{entry_id}")
    assert resp.status_code == 204


def test_log_consumption(client: TestClient) -> None:
    resp = client.post("/api/fuel/consumption", json={
        "fuel_type": "diesel",
        "quantity_used": 10,
        "unit": "liters",
        "purpose": "Generator",
        "used_by": "Alice",
    })
    assert resp.status_code == 201
    assert resp.json()["quantity_used"] == 10


def test_fuel_summary(client: TestClient) -> None:
    client.post("/api/fuel/storage", json={
        "fuel_type": "diesel", "quantity": 200, "unit": "liters",
    })
    client.post("/api/fuel/consumption", json={
        "fuel_type": "diesel", "quantity_used": 50, "unit": "liters",
    })

    resp = client.get("/api/fuel/summary")
    assert resp.status_code == 200
    diesel = next(s for s in resp.json() if s["fuel_type"] == "diesel")
    assert diesel["total_stored"] == 200
    assert diesel["total_consumed"] == 50
    assert diesel["net_available"] == 150


def test_days_of_supply(client: TestClient) -> None:
    resp = client.get("/api/fuel/days-of-supply")
    assert resp.status_code == 200
    assert len(resp.json()) == 6  # All fuel types


def test_low_fuel_alerts(client: TestClient) -> None:
    resp = client.get("/api/fuel/low-fuel")
    assert resp.status_code == 200


# --- Generators ---

def test_create_and_list_generators(client: TestClient) -> None:
    _create_generator(client)
    _create_generator(client, name="Diesel Gen", fuel_type="diesel", rated_kw=5.0)

    resp = client.get("/api/generators")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_and_update_generator(client: TestClient) -> None:
    gen = _create_generator(client)
    resp = client.get(f"/api/generators/{gen['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Honda EU2200i"

    resp = client.put(f"/api/generators/{gen['id']}", json={"location": "Shed B"})
    assert resp.status_code == 200
    assert resp.json()["location"] == "Shed B"


def test_delete_generator(client: TestClient) -> None:
    gen = _create_generator(client)
    resp = client.delete(f"/api/generators/{gen['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/generators/{gen['id']}")
    assert resp.status_code == 404


def test_log_runtime(client: TestClient) -> None:
    gen = _create_generator(client)
    resp = client.post("/api/generators/runtime", json={
        "generator_id": gen["id"],
        "start_time": "2026-03-07 08:00:00",
        "end_time": "2026-03-07 12:00:00",
        "fuel_consumed": 8.0,
        "load_percent": 75,
    })
    assert resp.status_code == 201
    assert resp.json()["fuel_consumed"] == 8.0

    # Check total runtime was updated
    resp = client.get(f"/api/generators/{gen['id']}")
    assert resp.json()["total_runtime_hours"] > 0


def test_runtime_history(client: TestClient) -> None:
    gen = _create_generator(client)
    client.post("/api/generators/runtime", json={
        "generator_id": gen["id"],
        "start_time": "2026-03-07 08:00:00",
        "end_time": "2026-03-07 10:00:00",
        "fuel_consumed": 4.0,
        "load_percent": 50,
    })

    resp = client.get(f"/api/generators/runtime/{gen['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_fuel_efficiency(client: TestClient) -> None:
    gen = _create_generator(client)
    client.post("/api/generators/runtime", json={
        "generator_id": gen["id"],
        "start_time": "2026-03-07 08:00:00",
        "end_time": "2026-03-07 12:00:00",
        "fuel_consumed": 8.0,
        "load_percent": 75,
    })

    resp = client.get(f"/api/generators/efficiency/{gen['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_fuel_consumed"] == 8.0
    assert data["kwh_per_liter"] >= 0


def test_generator_maintenance_schedule(client: TestClient) -> None:
    gen = _create_generator(client)
    resp = client.post("/api/generators/maintenance", json={
        "generator_id": gen["id"],
        "task": "Oil Change",
        "interval_hours": 100,
    })
    assert resp.status_code == 201

    resp = client.get(f"/api/generators/maintenance/{gen['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_complete_generator_maintenance(client: TestClient) -> None:
    gen = _create_generator(client, total_runtime_hours=150)
    sched = client.post("/api/generators/maintenance", json={
        "generator_id": gen["id"],
        "task": "Oil Change",
        "interval_hours": 100,
    }).json()

    resp = client.post(f"/api/generators/maintenance/{sched['id']}/complete", json={
        "performed_by": "Bob",
        "notes": "Used synthetic oil",
    })
    assert resp.status_code == 200
    assert resp.json()["last_performed_hours"] == 150

    resp = client.get(f"/api/generators/maintenance-history/{gen['id']}")
    assert len(resp.json()) == 1


def test_maintenance_due(client: TestClient) -> None:
    gen = _create_generator(client, total_runtime_hours=250)
    client.post("/api/generators/maintenance", json={
        "generator_id": gen["id"],
        "task": "Oil Change",
        "interval_hours": 100,
        "last_performed_hours": 100,
    })

    resp = client.get("/api/generators/maintenance-due")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["hours_overdue"] == 50


# --- Budget ---

def test_create_and_list_loads(client: TestClient) -> None:
    resp = client.post("/api/budget/loads", json={
        "name": "Radio Equipment",
        "watts_draw": 50,
        "priority": "critical",
        "hours_per_day": 24,
    })
    assert resp.status_code == 201
    assert resp.json()["priority"] == "critical"

    resp = client.get("/api/budget/loads")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_filter_loads_by_priority(client: TestClient) -> None:
    client.post("/api/budget/loads", json={
        "name": "Lights", "watts_draw": 100, "priority": "important", "hours_per_day": 8,
    })
    client.post("/api/budget/loads", json={
        "name": "TV", "watts_draw": 150, "priority": "optional", "hours_per_day": 4,
    })

    resp = client.get("/api/budget/loads?priority=important")
    assert len(resp.json()) == 1


def test_update_load(client: TestClient) -> None:
    load = client.post("/api/budget/loads", json={
        "name": "Pump", "watts_draw": 200, "priority": "important", "hours_per_day": 2,
    }).json()

    resp = client.put(f"/api/budget/loads/{load['id']}", json={"hours_per_day": 4})
    assert resp.status_code == 200
    assert resp.json()["hours_per_day"] == 4


def test_delete_load(client: TestClient) -> None:
    load = client.post("/api/budget/loads", json={
        "name": "Fan", "watts_draw": 75, "priority": "optional", "hours_per_day": 8,
    }).json()

    resp = client.delete(f"/api/budget/loads/{load['id']}")
    assert resp.status_code == 204


def test_demand_calculation(client: TestClient) -> None:
    client.post("/api/budget/loads", json={
        "name": "Radio", "watts_draw": 50, "priority": "critical", "hours_per_day": 24,
    })
    client.post("/api/budget/loads", json={
        "name": "Lights", "watts_draw": 100, "priority": "important", "hours_per_day": 8,
    })

    resp = client.get("/api/budget/demand")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_wh_per_day"] == (50 * 24) + (100 * 8)
    assert data["by_priority"]["critical"] == 1200
    assert data["by_priority"]["important"] == 800


def test_supply_calculation(client: TestClient) -> None:
    resp = client.get("/api/budget/supply")
    assert resp.status_code == 200
    data = resp.json()
    assert "solar_wh_per_day" in data
    assert "battery_capacity_wh" in data
    assert "generator_wh_per_day_max" in data


def test_budget_analysis(client: TestClient) -> None:
    resp = client.get("/api/budget/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert "demand" in data
    assert "supply" in data
    assert "surplus_wh" in data
    assert data["status"] in ("surplus", "deficit")


def test_load_shedding_no_deficit(client: TestClient) -> None:
    resp = client.get("/api/budget/load-shedding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["needed"] is False


def test_load_shedding_with_deficit(client: TestClient) -> None:
    # Create loads with no supply -> deficit
    client.post("/api/budget/loads", json={
        "name": "Radio", "watts_draw": 50, "priority": "critical", "hours_per_day": 24,
    })
    client.post("/api/budget/loads", json={
        "name": "Lights", "watts_draw": 100, "priority": "important", "hours_per_day": 12,
    })
    client.post("/api/budget/loads", json={
        "name": "TV", "watts_draw": 200, "priority": "optional", "hours_per_day": 6,
    })

    resp = client.get("/api/budget/load-shedding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["needed"] is True
    assert data["deficit_wh"] > 0
    # Optional loads should be cut first
    assert data["cuts"][0]["priority"] == "optional"
