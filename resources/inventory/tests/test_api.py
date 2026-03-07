"""Tests for the General Inventory API."""

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


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with sample locations and items."""
    # Create locations
    client.post("/api/locations", json={"name": "Main Warehouse", "type": "warehouse"})
    client.post("/api/locations", json={"name": "Vehicle 1", "type": "vehicle"})

    # Create items
    client.post("/api/items", json={
        "name": "Rice (25kg bag)",
        "category": "food",
        "subcategory": "grains",
        "quantity": 50,
        "unit": "bags",
        "condition": "good",
        "location_id": 1,
    })
    client.post("/api/items", json={
        "name": "Diesel Fuel",
        "category": "fuel",
        "quantity": 200,
        "unit": "liters",
        "location_id": 1,
    })
    client.post("/api/items", json={
        "name": "Bandages",
        "category": "medical",
        "quantity": 5,
        "unit": "boxes",
        "condition": "new",
        "location_id": 2,
    })
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Items ---

def test_create_item(client: TestClient) -> None:
    resp = client.post("/api/items", json={
        "name": "Water Jugs",
        "category": "water",
        "quantity": 20,
        "unit": "count",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Water Jugs"
    assert data["category"] == "water"
    assert data["quantity"] == 20
    assert data["qr_code"].startswith("INV-")


def test_create_item_invalid_category(client: TestClient) -> None:
    resp = client.post("/api/items", json={
        "name": "Bad Item",
        "category": "invalid_cat",
        "quantity": 1,
    })
    assert resp.status_code == 400


def test_list_items(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/items")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 3


def test_list_items_filter_category(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/items?category=food")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["category"] == "food"


def test_list_items_filter_name(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/items?name=Rice")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1


def test_get_item(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/items/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Rice (25kg bag)"


def test_get_item_not_found(client: TestClient) -> None:
    resp = client.get("/api/items/999")
    assert resp.status_code == 404


def test_update_item(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/items/1", json={"quantity": 45})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 45


def test_delete_item(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/items/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/items/1")
    assert resp.status_code == 404


def test_batch_import(client: TestClient) -> None:
    resp = client.post("/api/items/batch", json={
        "items": [
            {"name": "Hammer", "category": "tools", "quantity": 5, "unit": "count"},
            {"name": "Nails (box)", "category": "building_materials", "quantity": 20, "unit": "boxes"},
        ],
        "performed_by": "admin",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 2
    assert len(data["errors"]) == 0


def test_batch_import_with_errors(client: TestClient) -> None:
    resp = client.post("/api/items/batch", json={
        "items": [
            {"name": "Good", "category": "tools", "quantity": 1},
            {"name": "Bad", "category": "invalid", "quantity": 1},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 1
    assert len(data["errors"]) == 1


# --- Scanning ---

def test_qr_lookup(seeded_client: TestClient) -> None:
    # Get item to find its QR code
    item = seeded_client.get("/api/items/1").json()
    qr_code = item["qr_code"]

    resp = seeded_client.get(f"/api/scanning/lookup?code={qr_code}")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_qr_lookup_not_found(client: TestClient) -> None:
    resp = client.get("/api/scanning/lookup?code=NONEXISTENT")
    assert resp.status_code == 404


def test_qr_generate(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/scanning/qr/1")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


# --- Consumption ---

def test_record_consumption(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/consumption", json={
        "item_id": 1,
        "quantity_consumed": 5,
        "consumed_by": "cook",
        "purpose": "weekly meal prep",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["previous_quantity"] == 50
    assert data["new_quantity"] == 45


def test_record_consumption_item_not_found(client: TestClient) -> None:
    resp = client.post("/api/consumption", json={
        "item_id": 999,
        "quantity_consumed": 1,
    })
    assert resp.status_code == 404


def test_record_consumption_negative(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/consumption", json={
        "item_id": 1,
        "quantity_consumed": -1,
    })
    assert resp.status_code == 400


def test_consumption_history(seeded_client: TestClient) -> None:
    seeded_client.post("/api/consumption", json={"item_id": 1, "quantity_consumed": 2})
    seeded_client.post("/api/consumption", json={"item_id": 1, "quantity_consumed": 3})

    resp = seeded_client.get("/api/consumption/history/1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_consumption_rate(seeded_client: TestClient) -> None:
    seeded_client.post("/api/consumption", json={"item_id": 1, "quantity_consumed": 10})

    resp = seeded_client.get("/api/consumption/rate/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_id"] == 1
    assert data["total_consumed_30d"] == 10
    assert data["daily_rate"] > 0


# --- Locations ---

def test_create_location(client: TestClient) -> None:
    resp = client.post("/api/locations", json={
        "name": "Bunker A",
        "type": "cache",
        "description": "Underground cache",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Bunker A"


def test_create_location_invalid_type(client: TestClient) -> None:
    resp = client.post("/api/locations", json={
        "name": "Bad",
        "type": "spaceship",
    })
    assert resp.status_code == 400


def test_create_location_duplicate_name(client: TestClient) -> None:
    client.post("/api/locations", json={"name": "Spot A", "type": "warehouse"})
    resp = client.post("/api/locations", json={"name": "Spot A", "type": "warehouse"})
    assert resp.status_code == 400


def test_list_locations(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/locations")
    assert resp.status_code == 200
    locs = resp.json()
    assert len(locs) == 2
    # Should include item counts
    warehouse = next(l for l in locs if l["name"] == "Main Warehouse")
    assert warehouse["item_count"] == 2


def test_location_items(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/locations/1/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_transfer_item(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/locations/transfer", json={
        "item_id": 1,
        "to_location_id": 2,
        "transferred_by": "logistics",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["from_location"] == "Main Warehouse"
    assert data["to_location"] == "Vehicle 1"

    # Verify item moved
    item = seeded_client.get("/api/items/1").json()
    assert item["location_id"] == 2


def test_delete_location_with_items(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/locations/1")
    assert resp.status_code == 400


def test_delete_empty_location(client: TestClient) -> None:
    client.post("/api/locations", json={"name": "Empty", "type": "cache"})
    resp = client.delete("/api/locations/1")
    assert resp.status_code == 200


# --- Alerts ---

def test_create_threshold(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/alerts/thresholds", json={
        "item_id": 3,
        "min_level": 10,
    })
    assert resp.status_code == 201


def test_create_category_threshold(client: TestClient) -> None:
    resp = client.post("/api/alerts/thresholds", json={
        "category": "food",
        "min_level": 20,
    })
    assert resp.status_code == 201


def test_create_threshold_no_target(client: TestClient) -> None:
    resp = client.post("/api/alerts/thresholds", json={"min_level": 5})
    assert resp.status_code == 400


def test_get_active_alerts(seeded_client: TestClient) -> None:
    # Bandages has quantity=5, default min_stock=10, so it should alert
    resp = seeded_client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    # At least bandages should be critical (5 < 10)
    bandage_alerts = [a for a in alerts if a["item_name"] == "Bandages"]
    assert len(bandage_alerts) == 1
    assert bandage_alerts[0]["alert_level"] == "critical"


def test_list_thresholds(seeded_client: TestClient) -> None:
    seeded_client.post("/api/alerts/thresholds", json={"category": "food", "min_level": 20})
    resp = seeded_client.get("/api/alerts/thresholds")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_delete_threshold(seeded_client: TestClient) -> None:
    seeded_client.post("/api/alerts/thresholds", json={"category": "food", "min_level": 20})
    resp = seeded_client.delete("/api/alerts/thresholds/1")
    assert resp.status_code == 200


# --- Audit ---

def test_audit_log_created_on_item_create(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/audit")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 3  # 3 items created in seeded_client
    create_entries = [e for e in entries if e["action"] == "create"]
    assert len(create_entries) == 3


def test_audit_log_filter_by_item(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/audit?item_id=1")
    assert resp.status_code == 200
    entries = resp.json()
    assert all(e["item_id"] == 1 for e in entries)


def test_audit_report(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/audit/report")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_entries"] >= 3
    assert any(a["action"] == "create" for a in data["by_action"])
