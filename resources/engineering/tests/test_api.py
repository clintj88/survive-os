"""Tests for the Engineering & Maintenance API."""

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


def _create_item(client: TestClient, **overrides) -> dict:
    data = {"name": "Well Pump", "category": "water", "location": "North Field", "condition": "good"}
    data.update(overrides)
    resp = client.post("/api/maintenance/items", json=data)
    assert resp.status_code == 201
    return resp.json()


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_create_and_list_items(client: TestClient) -> None:
    _create_item(client)
    _create_item(client, name="Solar Array", category="power")

    resp = client.get("/api/maintenance/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get("/api/maintenance/items?category=water")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_and_update_item(client: TestClient) -> None:
    item = _create_item(client)
    resp = client.get(f"/api/maintenance/items/{item['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Well Pump"

    resp = client.put(f"/api/maintenance/items/{item['id']}", json={"condition": "poor"})
    assert resp.status_code == 200
    assert resp.json()["condition"] == "poor"


def test_delete_item(client: TestClient) -> None:
    item = _create_item(client)
    resp = client.delete(f"/api/maintenance/items/{item['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/api/maintenance/items/{item['id']}")
    assert resp.status_code == 404


def test_create_schedule(client: TestClient) -> None:
    item = _create_item(client)
    resp = client.post("/api/maintenance/schedules", json={
        "item_id": item["id"],
        "task_description": "Check pump pressure",
        "frequency_days": 30,
    })
    assert resp.status_code == 201
    assert resp.json()["task_description"] == "Check pump pressure"


def test_overdue_schedules(client: TestClient) -> None:
    item = _create_item(client)
    client.post("/api/maintenance/schedules", json={
        "item_id": item["id"],
        "task_description": "Oil change",
        "frequency_days": 30,
        "next_due": "2020-01-01",
    })

    resp = client.get("/api/maintenance/overdue")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_complete_maintenance(client: TestClient) -> None:
    item = _create_item(client)
    sched = client.post("/api/maintenance/schedules", json={
        "item_id": item["id"],
        "task_description": "Filter replacement",
        "frequency_days": 90,
        "next_due": "2020-01-01",
    }).json()

    resp = client.post(f"/api/maintenance/schedules/{sched['id']}/complete", json={
        "performed_by": "Alice",
        "notes": "Replaced with new filter",
    })
    assert resp.status_code == 200
    assert resp.json()["last_performed"] is not None

    resp = client.get(f"/api/maintenance/history?item_id={item['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_parts_crud(client: TestClient) -> None:
    resp = client.post("/api/parts", json={
        "part_number": "FLT-001",
        "name": "Oil Filter",
        "category": "filters",
        "fits_equipment": ["Generator A", "Truck B"],
        "salvage_sources": ["Old Generator"],
        "quantity_on_hand": 5,
    })
    assert resp.status_code == 201
    part = resp.json()
    assert part["name"] == "Oil Filter"
    assert part["fits_equipment"] == ["Generator A", "Truck B"]

    resp = client.get(f"/api/parts/{part['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/parts")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_parts_search(client: TestClient) -> None:
    client.post("/api/parts", json={
        "part_number": "BLT-001",
        "name": "Drive Belt",
        "fits_equipment": ["Generator A", "Water Pump"],
        "salvage_sources": ["Broken Pump"],
    })
    resp = client.get("/api/parts/search?equipment=Generator")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_parts_cross_reference(client: TestClient) -> None:
    client.post("/api/parts", json={
        "part_number": "BRG-001",
        "name": "Bearing 6204",
        "fits_equipment": ["Water Pump", "Generator"],
        "salvage_sources": ["Old Motor", "Broken Fan"],
    })
    resp = client.get("/api/parts/cross-reference?from_equipment=Old Motor&to_equipment=Water Pump")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_calculator_lumber(client: TestClient) -> None:
    resp = client.post("/api/calculator/lumber", json={
        "length_ft": 8, "width_in": 6, "thickness_in": 2,
    })
    assert resp.status_code == 200
    assert resp.json()["board_feet"] == 8.0

    resp = client.post("/api/calculator/lumber", json={
        "wall_length_ft": 12, "spacing_in": 16,
    })
    assert resp.status_code == 200
    assert resp.json()["stud_count"] == 10


def test_calculator_concrete(client: TestClient) -> None:
    resp = client.post("/api/calculator/concrete", json={
        "length_ft": 10, "width_ft": 10, "depth_in": 4, "shape": "slab",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["volume_cubic_yards"] > 0
    assert data["bags_60lb"] > 0


def test_calculator_roofing(client: TestClient) -> None:
    resp = client.post("/api/calculator/roofing", json={
        "length_ft": 30, "width_ft": 20, "pitch": 4,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["area_sq_ft"] > 600
    assert data["shingle_bundles"] > 0


def test_calculator_fencing(client: TestClient) -> None:
    resp = client.post("/api/calculator/fencing", json={
        "perimeter_ft": 400, "post_spacing_ft": 8, "wire_strands": 4,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["post_count"] == 51
    assert data["wire_length_ft"] == 1600


def test_calculator_paint(client: TestClient) -> None:
    resp = client.post("/api/calculator/paint", json={
        "walls": [{"length": 12, "height": 8}, {"length": 12, "height": 8}],
        "coats": 2, "doors": 1, "windows": 2,
    })
    assert resp.status_code == 200
    assert resp.json()["gallons_needed"] > 0


def test_chemistry_crud(client: TestClient) -> None:
    resp = client.post("/api/chemistry", json={
        "name": "Test Soap",
        "category": "cleaning",
        "ingredients": [{"name": "lye", "quantity": "1oz"}],
        "procedure": ["Mix", "Pour"],
        "safety_notes": "Wear gloves",
        "yield_amount": "1 bar",
        "difficulty": "easy",
    })
    assert resp.status_code == 201
    recipe = resp.json()
    assert recipe["name"] == "Test Soap"

    resp = client.get(f"/api/chemistry/{recipe['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/chemistry")
    assert len(resp.json()) >= 1


def test_chemistry_search(client: TestClient) -> None:
    client.post("/api/chemistry", json={
        "name": "Vinegar Pickle",
        "category": "preservation",
        "ingredients": [{"name": "vinegar", "quantity": "1 cup"}],
        "procedure": ["Pour"],
    })
    resp = client.get("/api/chemistry/search?q=vinegar")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_guides_crud(client: TestClient) -> None:
    resp = client.post("/api/guides", json={
        "title": "Solar Setup",
        "category": "solar",
        "content": "# Solar\nHow to set up solar panels.",
        "parts_needed": ["panels", "inverter"],
        "difficulty": "hard",
    })
    assert resp.status_code == 201
    guide = resp.json()
    assert guide["title"] == "Solar Setup"

    resp = client.get(f"/api/guides/{guide['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/guides/search?q=solar")
    assert len(resp.json()) >= 1


def test_drawings_crud(client: TestClient) -> None:
    resp = client.post("/api/drawings", json={
        "title": "Water System Layout",
        "description": "Main distribution system",
        "file_path": "/drawings/water-system.pdf",
        "category": "plumbing",
    })
    assert resp.status_code == 201
    drawing = resp.json()
    assert drawing["title"] == "Water System Layout"

    resp = client.get(f"/api/drawings/{drawing['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/drawings/search?q=water")
    assert len(resp.json()) >= 1
