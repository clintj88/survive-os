"""Tests for the Tool Library API."""

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


def _create_tool(client: TestClient, **overrides) -> dict:
    data = {
        "name": "Claw Hammer",
        "category": "hand_tools",
        "description": "16oz steel hammer",
        "condition": "good",
        "location": "Shed A",
    }
    data.update(overrides)
    resp = client.post("/api/tools", json=data)
    assert resp.status_code == 201
    return resp.json()


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Tool Inventory ---

def test_create_and_list_tools(client: TestClient) -> None:
    _create_tool(client)
    _create_tool(client, name="Drill", category="power_tools")

    resp = client.get("/api/tools")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get("/api/tools?category=hand_tools")
    assert len(resp.json()) == 1


def test_get_and_update_tool(client: TestClient) -> None:
    tool = _create_tool(client)
    resp = client.get(f"/api/tools/{tool['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Claw Hammer"

    resp = client.put(f"/api/tools/{tool['id']}", json={"condition": "fair"})
    assert resp.status_code == 200
    assert resp.json()["condition"] == "fair"


def test_delete_tool(client: TestClient) -> None:
    tool = _create_tool(client)
    resp = client.delete(f"/api/tools/{tool['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/tools/{tool['id']}")
    assert resp.status_code == 404


def test_filter_tools_by_condition(client: TestClient) -> None:
    _create_tool(client, condition="excellent")
    _create_tool(client, name="Old Saw", condition="poor")

    resp = client.get("/api/tools?condition=excellent")
    assert len(resp.json()) == 1
    assert resp.json()[0]["condition"] == "excellent"


def test_search_tools(client: TestClient) -> None:
    _create_tool(client)
    _create_tool(client, name="Screwdriver", description="Phillips head")

    resp = client.get("/api/tools?search=Phillips")
    assert len(resp.json()) == 1


def test_filter_by_status(client: TestClient) -> None:
    tool = _create_tool(client)
    _create_tool(client, name="Wrench")

    client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Alice",
        "expected_return_date": "2030-01-01",
    })

    resp = client.get("/api/tools?status=available")
    assert len(resp.json()) == 1

    resp = client.get("/api/tools?status=checked_out")
    assert len(resp.json()) == 1


# --- Checkouts ---

def test_checkout_and_checkin(client: TestClient) -> None:
    tool = _create_tool(client)
    resp = client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Alice",
        "expected_return_date": "2030-01-15",
    })
    assert resp.status_code == 201
    checkout = resp.json()
    assert checkout["borrowed_by"] == "Alice"
    assert checkout["condition_at_checkout"] == "good"

    # Tool should be checked out
    resp = client.get(f"/api/tools/{tool['id']}")
    assert resp.json()["status"] == "checked_out"

    # Cannot checkout again
    resp = client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Bob",
        "expected_return_date": "2030-01-20",
    })
    assert resp.status_code == 409

    # Check in
    resp = client.post(f"/api/checkouts/{checkout['id']}/checkin", json={
        "condition_at_return": "fair",
    })
    assert resp.status_code == 200
    assert resp.json()["condition_at_return"] == "fair"

    # Tool should be available again with updated condition
    resp = client.get(f"/api/tools/{tool['id']}")
    assert resp.json()["status"] == "available"
    assert resp.json()["condition"] == "fair"


def test_overdue_checkouts(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Alice",
        "expected_return_date": "2020-01-01",
    })

    resp = client.get("/api/checkouts/overdue")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_checkouts_by_person(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Bob",
        "expected_return_date": "2030-01-01",
    })

    resp = client.get("/api/checkouts/by-person/Bob")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/checkouts/by-person/Nobody")
    assert len(resp.json()) == 0


def test_list_checkouts_filter(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Alice",
        "expected_return_date": "2030-01-01",
    })

    resp = client.get("/api/checkouts?active=true")
    assert len(resp.json()) == 1

    resp = client.get("/api/checkouts?active=false")
    assert len(resp.json()) == 0


# --- Maintenance ---

def test_create_and_list_maintenance_tasks(client: TestClient) -> None:
    tool = _create_tool(client)
    resp = client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "sharpen",
        "frequency_days": 30,
    })
    assert resp.status_code == 201
    assert resp.json()["task"] == "sharpen"

    resp = client.get("/api/maintenance/tasks")
    assert len(resp.json()) == 1

    resp = client.get(f"/api/maintenance/tasks?tool_id={tool['id']}")
    assert len(resp.json()) == 1


def test_complete_maintenance(client: TestClient) -> None:
    tool = _create_tool(client)
    task = client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "oil",
        "frequency_days": 60,
        "next_due": "2020-01-01",
    }).json()

    resp = client.post(f"/api/maintenance/tasks/{task['id']}/complete", json={
        "performed_by": "Alice",
        "notes": "Applied 3-in-1 oil",
    })
    assert resp.status_code == 200
    assert resp.json()["last_performed"] is not None

    resp = client.get(f"/api/maintenance/history?tool_id={tool['id']}")
    assert len(resp.json()) == 1


def test_overdue_maintenance(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "clean",
        "frequency_days": 14,
        "next_due": "2020-01-01",
    })

    resp = client.get("/api/maintenance/overdue")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_condition_alerts(client: TestClient) -> None:
    tool = _create_tool(client, condition="good")
    client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "clean",
        "frequency_days": 7,
        "next_due": "2020-01-01",
    })

    resp = client.get("/api/maintenance/condition-alerts")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert resp.json()[0]["tool_id"] == tool["id"]


def test_update_maintenance_task(client: TestClient) -> None:
    tool = _create_tool(client)
    task = client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "sharpen",
        "frequency_days": 30,
    }).json()

    resp = client.put(f"/api/maintenance/tasks/{task['id']}", json={
        "frequency_days": 14,
    })
    assert resp.status_code == 200
    assert resp.json()["frequency_days"] == 14


def test_delete_maintenance_task(client: TestClient) -> None:
    tool = _create_tool(client)
    task = client.post("/api/maintenance/tasks", json={
        "tool_id": tool["id"],
        "task": "calibrate",
        "frequency_days": 90,
    }).json()

    resp = client.delete(f"/api/maintenance/tasks/{task['id']}")
    assert resp.status_code == 204


# --- Usage ---

def test_usage_stats(client: TestClient) -> None:
    tool = _create_tool(client)

    resp = client.get(f"/api/usage/stats/{tool['id']}")
    assert resp.status_code == 200
    assert resp.json()["total_checkouts"] == 0


def test_wear_prediction(client: TestClient) -> None:
    tool = _create_tool(client)

    resp = client.get(f"/api/usage/wear/{tool['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "Claw Hammer"
    assert data["wear_percentage"] == 0.0
    assert data["remaining_life_days"] > 0


def test_most_used(client: TestClient) -> None:
    tool = _create_tool(client)
    # Create a checkout record
    co = client.post("/api/checkouts", json={
        "tool_id": tool["id"],
        "borrowed_by": "Alice",
        "expected_return_date": "2030-01-01",
    }).json()
    client.post(f"/api/checkouts/{co['id']}/checkin", json={
        "condition_at_return": "good",
    })

    resp = client.get("/api/usage/most-used")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_replacement_alerts(client: TestClient) -> None:
    resp = client.get("/api/usage/replacement-alerts")
    assert resp.status_code == 200


# --- Reservations ---

def test_create_and_list_reservations(client: TestClient) -> None:
    tool = _create_tool(client)
    resp = client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Alice",
        "date_needed": "2030-06-01",
        "duration_days": 3,
        "purpose": "Garden work",
    })
    assert resp.status_code == 201
    res = resp.json()
    assert res["reserved_by"] == "Alice"

    resp = client.get("/api/reservations")
    assert len(resp.json()) == 1


def test_reservation_conflict(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Alice",
        "date_needed": "2030-06-01",
        "duration_days": 5,
    })

    resp = client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Bob",
        "date_needed": "2030-06-03",
        "duration_days": 2,
    })
    assert resp.status_code == 409


def test_cancel_reservation(client: TestClient) -> None:
    tool = _create_tool(client)
    res = client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Alice",
        "date_needed": "2030-06-01",
    }).json()

    resp = client.post(f"/api/reservations/{res['id']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_upcoming_reservations(client: TestClient) -> None:
    resp = client.get("/api/reservations/upcoming?days=365")
    assert resp.status_code == 200


def test_reservation_queue(client: TestClient) -> None:
    tool = _create_tool(client)
    client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Alice",
        "date_needed": "2030-06-01",
        "duration_days": 2,
    })
    client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Bob",
        "date_needed": "2030-06-10",
        "duration_days": 1,
    })

    resp = client.get(f"/api/reservations/queue/{tool['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_reservation(client: TestClient) -> None:
    tool = _create_tool(client)
    res = client.post("/api/reservations", json={
        "tool_id": tool["id"],
        "reserved_by": "Alice",
        "date_needed": "2030-06-01",
        "duration_days": 2,
    }).json()

    resp = client.put(f"/api/reservations/{res['id']}", json={
        "purpose": "Fence repair",
    })
    assert resp.status_code == 200
    assert resp.json()["purpose"] == "Fence repair"
