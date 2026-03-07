"""Tests for the seed bank API."""

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_lot(client):
    resp = client.post("/api/inventory/lots", json={
        "name": "Cherokee Purple",
        "species": "tomato",
        "variety": "Cherokee Purple",
        "quantity": 200,
        "unit": "count",
        "source": "Baker Creek",
        "date_collected": "2025-06-15",
        "storage_location": "Vault A",
        "storage_temp": 10,
        "storage_humidity": 35,
    })
    assert resp.status_code == 201
    return resp.json()


# ---- Health ----

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# ---- Inventory ----

def test_create_lot(client):
    resp = client.post("/api/inventory/lots", json={
        "name": "Brandywine",
        "species": "tomato",
        "variety": "Brandywine",
        "quantity": 100,
        "source": "Seed Savers",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Brandywine"
    assert data["quantity"] == 100


def test_list_lots(client, sample_lot):
    resp = client.get("/api/inventory/lots")
    assert resp.status_code == 200
    lots = resp.json()
    assert len(lots) >= 1


def test_get_lot(client, sample_lot):
    resp = client.get(f"/api/inventory/lots/{sample_lot['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Cherokee Purple"


def test_update_lot(client, sample_lot):
    resp = client.put(f"/api/inventory/lots/{sample_lot['id']}", json={
        "notes": "Heirloom variety",
    })
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Heirloom variety"


def test_delete_lot(client, sample_lot):
    resp = client.delete(f"/api/inventory/lots/{sample_lot['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/inventory/lots/{sample_lot['id']}")
    assert resp.status_code == 404


def test_search_lots(client, sample_lot):
    resp = client.get("/api/inventory/lots?search=Cherokee")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_filter_by_species(client, sample_lot):
    resp = client.get("/api/inventory/lots?species=tomato")
    assert resp.status_code == 200
    assert all(l["species"] == "tomato" for l in resp.json())


# ---- Ledger ----

def test_ledger_deposit(client, sample_lot):
    resp = client.post(f"/api/inventory/lots/{sample_lot['id']}/ledger", json={
        "type": "deposit",
        "amount": 50,
        "reason": "Harvest",
    })
    assert resp.status_code == 201
    lot = client.get(f"/api/inventory/lots/{sample_lot['id']}").json()
    assert lot["quantity"] == 250


def test_ledger_withdrawal(client, sample_lot):
    resp = client.post(f"/api/inventory/lots/{sample_lot['id']}/ledger", json={
        "type": "withdrawal",
        "amount": 30,
        "reason": "Planting",
    })
    assert resp.status_code == 201
    lot = client.get(f"/api/inventory/lots/{sample_lot['id']}").json()
    assert lot["quantity"] == 170


def test_ledger_overdraft(client, sample_lot):
    resp = client.post(f"/api/inventory/lots/{sample_lot['id']}/ledger", json={
        "type": "withdrawal",
        "amount": 9999,
        "reason": "Too much",
    })
    assert resp.status_code == 400


def test_get_ledger(client, sample_lot):
    resp = client.get(f"/api/inventory/lots/{sample_lot['id']}/ledger")
    assert resp.status_code == 200
    # Should have the initial deposit from creation
    assert len(resp.json()) >= 1


def test_low_stock_alert(client):
    client.post("/api/inventory/lots", json={
        "name": "Low Stock",
        "species": "onion",
        "quantity": 10,
        "low_stock_threshold": 50,
    })
    resp = client.get("/api/inventory/alerts/low-stock")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ---- Germination ----

def test_create_germination_test(client, sample_lot):
    resp = client.post("/api/germination/tests", json={
        "lot_id": sample_lot["id"],
        "sample_size": 100,
        "germination_count": 85,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["germination_rate"] == 85.0


def test_list_germination_tests(client, sample_lot):
    client.post("/api/germination/tests", json={
        "lot_id": sample_lot["id"],
        "sample_size": 50,
        "germination_count": 40,
    })
    resp = client.get("/api/germination/tests")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_germination_by_lot(client, sample_lot):
    client.post("/api/germination/tests", json={
        "lot_id": sample_lot["id"],
        "sample_size": 50,
        "germination_count": 45,
    })
    resp = client.get(f"/api/germination/tests?lot_id={sample_lot['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_germination_invalid(client, sample_lot):
    resp = client.post("/api/germination/tests", json={
        "lot_id": sample_lot["id"],
        "sample_size": 10,
        "germination_count": 20,
    })
    assert resp.status_code == 400


def test_species_history(client, sample_lot):
    client.post("/api/germination/tests", json={
        "lot_id": sample_lot["id"],
        "sample_size": 50,
        "germination_count": 40,
    })
    resp = client.get("/api/germination/history/tomato")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_germination_reminders(client, sample_lot):
    resp = client.get("/api/germination/reminders")
    assert resp.status_code == 200


# ---- Viability ----

def test_predict_viability(client, sample_lot):
    resp = client.get(f"/api/viability/predict/{sample_lot['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_viability_pct" in data
    assert data["status"] in ("green", "yellow", "red")


def test_viability_dashboard(client, sample_lot):
    resp = client.get("/api/viability/dashboard")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_viability_alerts(client):
    # Create an old lot that should have low viability
    client.post("/api/inventory/lots", json={
        "name": "Old Onions",
        "species": "onion",
        "quantity": 100,
        "date_collected": "2020-01-01",
    })
    resp = client.get("/api/viability/alerts")
    assert resp.status_code == 200


def test_species_viability_data(client):
    resp = client.get("/api/viability/species-data")
    assert resp.status_code == 200
    data = resp.json()
    assert "tomato" in data
    assert "onion" in data


# ---- Diversity ----

def test_diversity_scores(client):
    for i, source in enumerate(["Baker Creek", "Seed Savers", "Local Farm"]):
        client.post("/api/inventory/lots", json={
            "name": f"Tomato {i}",
            "species": "tomato",
            "quantity": 100,
            "source": source,
        })
    resp = client.get("/api/diversity/scores")
    assert resp.status_code == 200
    scores = resp.json()
    tomato = next(s for s in scores if s["species"] == "tomato")
    assert tomato["distinct_sources"] == 3
    assert tomato["status"] == "healthy"


def test_diversity_alerts(client):
    client.post("/api/inventory/lots", json={
        "name": "Lonely Onion",
        "species": "onion",
        "quantity": 100,
        "source": "Only Source",
    })
    resp = client.get("/api/diversity/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert any(a["species"] == "onion" for a in alerts)


def test_species_diversity_detail(client, sample_lot):
    resp = client.get("/api/diversity/species/tomato")
    assert resp.status_code == 200
    data = resp.json()
    assert data["species"] == "tomato"
    assert data["total_lots"] >= 1


# ---- Exchange ----

def test_create_exchange_listing(client):
    resp = client.post("/api/exchange/listings", json={
        "type": "offer",
        "species": "tomato",
        "variety": "Brandywine",
        "quantity_available": 50,
        "description": "Heirloom seeds, organic",
        "contact": "radio ch 5",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "offer"
    assert data["status"] == "active"


def test_list_exchange_listings(client):
    client.post("/api/exchange/listings", json={
        "type": "offer",
        "species": "bean",
        "quantity_available": 100,
    })
    resp = client.get("/api/exchange/listings")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_filter_exchange_by_type(client):
    client.post("/api/exchange/listings", json={"type": "offer", "species": "bean"})
    client.post("/api/exchange/listings", json={"type": "request", "species": "corn"})
    offers = client.get("/api/exchange/listings?type=offer").json()
    assert all(l["type"] == "offer" for l in offers)


def test_update_exchange_listing(client):
    resp = client.post("/api/exchange/listings", json={
        "type": "offer",
        "species": "pea",
        "quantity_available": 200,
    })
    listing_id = resp.json()["id"]
    resp = client.put(f"/api/exchange/listings/{listing_id}", json={
        "status": "fulfilled",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "fulfilled"


def test_delete_exchange_listing(client):
    resp = client.post("/api/exchange/listings", json={
        "type": "request",
        "species": "lettuce",
    })
    listing_id = resp.json()["id"]
    resp = client.delete(f"/api/exchange/listings/{listing_id}")
    assert resp.status_code == 204
