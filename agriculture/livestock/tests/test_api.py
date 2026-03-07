"""Tests for the Livestock Management API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    """Set up a fresh database for each test."""
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with sample animals and data."""
    # Create grandparents
    client.post("/api/animals", json={
        "name": "Grand Sire", "species": "cattle", "breed": "Angus",
        "sex": "male", "birth_date": "2018-01-01",
    })
    client.post("/api/animals", json={
        "name": "Grand Dam", "species": "cattle", "breed": "Angus",
        "sex": "female", "birth_date": "2018-03-15",
    })
    # Create parents (sire with lineage)
    client.post("/api/animals", json={
        "name": "Bull A", "species": "cattle", "breed": "Angus",
        "sex": "male", "birth_date": "2020-04-01", "sire_id": 1, "dam_id": 2,
    })
    client.post("/api/animals", json={
        "name": "Cow B", "species": "cattle", "breed": "Hereford",
        "sex": "female", "birth_date": "2020-06-15", "sire_id": 1, "dam_id": 2,
    })
    # Create another unrelated cow
    client.post("/api/animals", json={
        "name": "Cow C", "species": "cattle", "breed": "Angus",
        "sex": "female", "birth_date": "2021-01-10",
    })
    # Seed feed data
    from seed.feed_data import seed_feed_data
    seed_feed_data()
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Animals ---

def test_create_animal(client: TestClient) -> None:
    resp = client.post("/api/animals", json={
        "name": "Bessie", "species": "cattle", "breed": "Holstein",
        "sex": "female", "birth_date": "2022-03-01",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Bessie"
    assert data["species"] == "cattle"
    assert data["id"] == 1


def test_list_animals(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_list_animals_filter_species(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals?species=cattle")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_list_animals_filter_status(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals?status=active")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_get_animal(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Grand Sire"


def test_get_animal_not_found(client: TestClient) -> None:
    resp = client.get("/api/animals/999")
    assert resp.status_code == 404


def test_update_animal(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/animals/1", json={"name": "Updated Bull"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Bull"


def test_delete_animal(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/animals/5")
    assert resp.status_code == 204


def test_pedigree(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals/3/pedigree")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bull A"
    assert data["sire"]["name"] == "Grand Sire"
    assert data["dam"]["name"] == "Grand Dam"


def test_offspring(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/animals/1/offspring")
    assert resp.status_code == 200
    offspring = resp.json()
    assert len(offspring) == 2
    names = {o["name"] for o in offspring}
    assert "Bull A" in names
    assert "Cow B" in names


# --- Breeding ---

def test_create_breeding_event(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/breeding/events", json={
        "sire_id": 3, "dam_id": 5, "date_bred": "2025-06-01",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["sire_name"] == "Bull A"
    assert data["dam_name"] == "Cow C"
    assert data["expected_due_date"] is not None


def test_list_breeding_events(seeded_client: TestClient) -> None:
    seeded_client.post("/api/breeding/events", json={
        "sire_id": 3, "dam_id": 5, "date_bred": "2025-06-01",
    })
    resp = seeded_client.get("/api/breeding/events")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_breeding_event(seeded_client: TestClient) -> None:
    seeded_client.post("/api/breeding/events", json={
        "sire_id": 3, "dam_id": 5, "date_bred": "2025-06-01",
    })
    resp = seeded_client.put("/api/breeding/events/1", json={
        "outcome": "success", "offspring_count": 1,
    })
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "success"


def test_gestation_periods(client: TestClient) -> None:
    resp = client.get("/api/breeding/gestation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cattle"] == 283
    assert data["goat"] == 150


def test_gestation_calculator(client: TestClient) -> None:
    resp = client.get("/api/breeding/gestation/cattle?date_bred=2025-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["expected_due_date"] == "2025-10-11"
    assert data["gestation_days"] == 283


def test_inbreeding_coefficient(seeded_client: TestClient) -> None:
    # Bull A and Cow B share same parents (Grand Sire & Grand Dam)
    resp = seeded_client.get("/api/breeding/inbreeding?sire_id=3&dam_id=4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["coefficient"] > 0
    assert data["warning"] is True  # Full siblings -> high coefficient


def test_inbreeding_unrelated(seeded_client: TestClient) -> None:
    # Bull A and Cow C are unrelated
    resp = seeded_client.get("/api/breeding/inbreeding?sire_id=3&dam_id=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["coefficient"] == 0
    assert data["warning"] is False


def test_suggest_pairings(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/breeding/suggestions?species=cattle")
    assert resp.status_code == 200
    pairings = resp.json()
    assert len(pairings) > 0
    # Should be sorted by coefficient ascending
    assert pairings[0]["coefficient"] <= pairings[-1]["coefficient"]


# --- Feed ---

def test_feed_requirements(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/feed/requirements?species=cattle")
    assert resp.status_code == 200
    reqs = resp.json()
    assert len(reqs) >= 4


def test_feed_calculate(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/feed/calculate?species=cattle&weight_kg=500&production_stage=maintenance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["daily_dry_matter_kg"] == 10.0  # 500 * 2.0%
    assert data["species"] == "cattle"


def test_feed_types(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/feed/types")
    assert resp.status_code == 200
    assert len(resp.json()) >= 10


def test_feed_inventory_lifecycle(seeded_client: TestClient) -> None:
    # Create inventory
    resp = seeded_client.post("/api/feed/inventory?feed_type_id=1&quantity=100&low_threshold=20")
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 100

    # Update inventory
    resp = seeded_client.put("/api/feed/inventory/1", json={"quantity": 80})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 80

    # Check alerts (80 > 20 so no alert)
    resp = seeded_client.get("/api/feed/inventory/alerts")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_feed_consumption(seeded_client: TestClient) -> None:
    # Set up inventory
    seeded_client.post("/api/feed/inventory?feed_type_id=1&quantity=100&low_threshold=20")
    # Record consumption
    resp = seeded_client.post("/api/feed/consumption", json={
        "animal_id": 1, "feed_type_id": 1, "quantity": 5, "date": "2025-06-01",
    })
    assert resp.status_code == 201
    # Check inventory was deducted
    inv = seeded_client.get("/api/feed/inventory").json()
    assert inv[0]["quantity"] == 95


# --- Veterinary ---

def test_create_treatment(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/vet/treatments", json={
        "animal_id": 1, "date": "2025-06-01",
        "condition": "Limping", "treatment": "Hoof trim",
        "medication": "Penicillin", "dosage": "10ml",
        "administered_by": "Dr. Smith", "withdrawal_days": 14,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["condition"] == "Limping"
    assert data["withdrawal_end_date"] == "2025-06-15"


def test_list_treatments(seeded_client: TestClient) -> None:
    seeded_client.post("/api/vet/treatments", json={
        "animal_id": 1, "condition": "Fever", "treatment": "Antibiotics",
    })
    resp = seeded_client.get("/api/vet/treatments?animal_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_medication_lifecycle(seeded_client: TestClient) -> None:
    # Create medication
    resp = seeded_client.post("/api/vet/medications", json={
        "name": "Penicillin", "type": "antibiotic",
        "quantity": 50, "unit": "ml", "default_withdrawal_days": 14,
    })
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 50

    # Update medication
    resp = seeded_client.put("/api/vet/medications/1", json={"quantity": 40})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 40


def test_vaccination(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/vet/vaccinations", json={
        "animal_id": 1, "vaccine": "Blackleg",
        "date_given": "2025-06-01", "next_due_date": "2026-06-01",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["vaccine"] == "Blackleg"
    assert data["next_due_date"] == "2026-06-01"


def test_list_vaccinations(seeded_client: TestClient) -> None:
    seeded_client.post("/api/vet/vaccinations", json={
        "animal_id": 1, "vaccine": "Blackleg", "date_given": "2025-06-01",
    })
    resp = seeded_client.get("/api/vet/vaccinations?animal_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- Production ---

def test_create_production_record(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/production/records", json={
        "animal_id": 4, "type": "milk", "value": 22.5,
        "unit": "liters", "date": "2025-06-01",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "milk"
    assert data["value"] == 22.5


def test_list_production_records(seeded_client: TestClient) -> None:
    seeded_client.post("/api/production/records", json={
        "animal_id": 4, "type": "milk", "value": 22.5, "unit": "liters", "date": "2025-06-01",
    })
    resp = seeded_client.get("/api/production/records?type=milk")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_production_analytics(seeded_client: TestClient) -> None:
    for day in range(1, 4):
        seeded_client.post("/api/production/records", json={
            "animal_id": 4, "type": "milk", "value": 20 + day,
            "unit": "liters", "date": f"2025-06-{day:02d}",
        })
    resp = seeded_client.get("/api/production/analytics?type=milk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["count"] == 3
    assert data["summary"]["total"] == 66.0  # 21+22+23
    assert len(data["top_producers"]) == 1
    assert len(data["daily_totals"]) == 3


def test_feed_conversion_ratio(seeded_client: TestClient) -> None:
    # Set up feed inventory
    seeded_client.post("/api/feed/inventory?feed_type_id=1&quantity=1000&low_threshold=20")
    # Record feed consumption
    seeded_client.post("/api/feed/consumption", json={
        "animal_id": 3, "feed_type_id": 1, "quantity": 100, "date": "2025-06-01",
    })
    # Record weight measurements
    seeded_client.post("/api/production/records", json={
        "animal_id": 3, "type": "weight", "value": 300, "unit": "kg", "date": "2025-06-01",
    })
    seeded_client.post("/api/production/records", json={
        "animal_id": 3, "type": "weight", "value": 320, "unit": "kg", "date": "2025-06-30",
    })

    resp = seeded_client.get("/api/production/fcr?animal_id=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_feed_kg"] == 100
    assert data["weight_gain_kg"] == 20
    assert data["fcr"] == 5.0  # 100 / 20
