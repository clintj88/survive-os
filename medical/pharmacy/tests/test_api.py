"""Tests for the Pharmacy API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app
from seed.dosing_rules import seed_dosing_rules
from seed.interactions import seed_interactions
from seed.natural_medicine import seed_natural_medicines


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
    """Client with seed data loaded."""
    seed_interactions(execute, query)
    seed_natural_medicines(execute, query)
    seed_dosing_rules(execute, query)
    return client


@pytest.fixture
def med_client(client: TestClient) -> TestClient:
    """Client with a medication and lot created."""
    execute(
        """INSERT INTO medications (name, generic_name, category, form, strength, unit)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Amoxicillin", "Amoxicillin", "Antibiotic", "capsule", "500mg", "capsule"),
    )
    execute(
        """INSERT INTO inventory_lots
           (medication_id, lot_number, quantity, expiration_date, supplier, storage_location)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, "LOT-001", 100, "2027-12-31", "MedSupply Co", "Shelf A-1"),
    )
    execute(
        """INSERT INTO inventory_lots
           (medication_id, lot_number, quantity, expiration_date, supplier, storage_location)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, "LOT-002", 50, "2026-06-15", "MedSupply Co", "Shelf A-1"),
    )
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Medications ---

def test_create_medication(client: TestClient) -> None:
    resp = client.post("/api/inventory/medications", json={
        "name": "Ibuprofen",
        "generic_name": "Ibuprofen",
        "category": "NSAID",
        "form": "tablet",
        "strength": "200mg",
        "unit": "tablet",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ibuprofen"
    assert data["id"] == 1


def test_list_medications(med_client: TestClient) -> None:
    resp = med_client.get("/api/inventory/medications")
    assert resp.status_code == 200
    meds = resp.json()
    assert len(meds) == 1
    assert meds[0]["name"] == "Amoxicillin"
    assert meds[0]["total_stock"] == 150


def test_search_medications(med_client: TestClient) -> None:
    resp = med_client.get("/api/inventory/medications?search=amox")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = med_client.get("/api/inventory/medications?search=nonexistent")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_medication(med_client: TestClient) -> None:
    resp = med_client.get("/api/inventory/medications/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Amoxicillin"
    assert len(data["lots"]) == 2


def test_get_medication_not_found(client: TestClient) -> None:
    resp = client.get("/api/inventory/medications/999")
    assert resp.status_code == 404


def test_update_medication(med_client: TestClient) -> None:
    resp = med_client.put("/api/inventory/medications/1", json={
        "notes": "First-line antibiotic",
    })
    assert resp.status_code == 200
    assert resp.json()["notes"] == "First-line antibiotic"


def test_delete_medication(med_client: TestClient) -> None:
    resp = med_client.delete("/api/inventory/medications/1")
    assert resp.status_code == 204

    resp = med_client.get("/api/inventory/medications/1")
    assert resp.status_code == 404


# --- Inventory Lots ---

def test_create_lot(med_client: TestClient) -> None:
    resp = med_client.post("/api/inventory/lots", json={
        "medication_id": 1,
        "lot_number": "LOT-003",
        "quantity": 200,
        "expiration_date": "2028-01-01",
        "supplier": "PharmaCorp",
        "storage_location": "Shelf B-2",
    })
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 200


def test_create_lot_bad_medication(client: TestClient) -> None:
    resp = client.post("/api/inventory/lots", json={
        "medication_id": 999,
        "quantity": 100,
        "expiration_date": "2028-01-01",
    })
    assert resp.status_code == 400


def test_list_lots(med_client: TestClient) -> None:
    resp = med_client.get("/api/inventory/lots")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_lots_by_medication(med_client: TestClient) -> None:
    resp = med_client.get("/api/inventory/lots?medication_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- Dispensing ---

def test_dispense_medication(med_client: TestClient) -> None:
    # Create a prescription first
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.post("/api/inventory/dispense", json={
        "medication_id": 1,
        "quantity": 21,
        "prescription_id": 1,
        "dispensed_by": "Pharmacist Jones",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_dispensed"] == 21
    # Should dispense from LOT-002 first (earlier expiration - FIFO)
    assert data["dispensed"][0]["lot_id"] == 2


def test_dispense_insufficient_stock(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.post("/api/inventory/dispense", json={
        "medication_id": 1,
        "quantity": 999,
        "prescription_id": 1,
        "dispensed_by": "Pharmacist Jones",
    })
    assert resp.status_code == 400
    assert "Insufficient" in resp.json()["detail"]


def test_dispense_no_active_prescription(med_client: TestClient) -> None:
    resp = med_client.post("/api/inventory/dispense", json={
        "medication_id": 1,
        "quantity": 10,
        "prescription_id": 999,
        "dispensed_by": "Pharmacist Jones",
    })
    assert resp.status_code == 400


# --- Expiration ---

def test_get_expiring_medications(med_client: TestClient) -> None:
    # LOT-002 expires 2026-06-15, which is within 365 days of test date (2026-03-07)
    resp = med_client.get("/api/inventory/expiring?days=365")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


def test_get_expired_medications(client: TestClient) -> None:
    execute(
        """INSERT INTO medications (name, generic_name, category, form)
           VALUES (?, ?, ?, ?)""",
        ("Expired Med", "Expired", "Test", "tablet"),
    )
    execute(
        """INSERT INTO inventory_lots
           (medication_id, lot_number, quantity, expiration_date)
           VALUES (?, ?, ?, ?)""",
        (1, "EXP-001", 50, "2020-01-01"),
    )
    resp = client.get("/api/inventory/expired")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- Prescriptions ---

def test_create_prescription(med_client: TestClient) -> None:
    resp = med_client.post("/api/prescriptions", json={
        "patient_id": "patient-001",
        "medication_id": 1,
        "dosage": "500mg",
        "frequency": "3x daily",
        "duration": "7 days",
        "prescriber": "Dr. Smith",
        "refills_remaining": 2,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["medication_name"] == "Amoxicillin"


def test_list_prescriptions(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.get("/api/prescriptions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_prescriptions_by_patient(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.get("/api/prescriptions?patient_id=patient-001")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = med_client.get("/api/prescriptions?patient_id=nobody")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_prescription(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.get("/api/prescriptions/1")
    assert resp.status_code == 200
    assert resp.json()["patient_id"] == "patient-001"


def test_update_prescription(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber)
           VALUES (?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith"),
    )
    resp = med_client.put("/api/prescriptions/1", json={
        "status": "completed",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_active_prescriptions_by_patient(med_client: TestClient) -> None:
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("patient-001", 1, "500mg", "3x daily", "Dr. Smith", "active"),
    )
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("patient-001", 1, "250mg", "2x daily", "Dr. Smith", "completed"),
    )
    resp = med_client.get("/api/prescriptions/patient/patient-001/active")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- Drug Interactions ---

def test_check_interactions(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/interactions/check", json={
        "medications": ["Warfarin", "Ibuprofen"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["severity"] == "major"


def test_check_interactions_none(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/interactions/check", json={
        "medications": ["Amoxicillin", "Acetaminophen"],
    })
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_check_interactions_single_med(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/interactions/check", json={
        "medications": ["Warfarin"],
    })
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_interactions(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/interactions")
    assert resp.status_code == 200
    assert len(resp.json()) >= 50


def test_list_interactions_by_severity(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/interactions?severity=contraindicated")
    assert resp.status_code == 200
    data = resp.json()
    assert all(i["severity"] == "contraindicated" for i in data)


def test_check_patient_interactions(seeded_client: TestClient) -> None:
    # Create medication and prescription
    execute(
        """INSERT INTO medications (name, generic_name, category, form)
           VALUES (?, ?, ?, ?)""",
        ("Warfarin", "Warfarin", "Anticoagulant", "tablet"),
    )
    execute(
        """INSERT INTO prescriptions
           (patient_id, medication_id, dosage, frequency, prescriber, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("patient-001", 1, "5mg", "daily", "Dr. Smith", "active"),
    )
    resp = seeded_client.post("/api/interactions/check-patient", json={
        "patient_id": "patient-001",
        "new_medication": "Ibuprofen",
    })
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# --- Natural Medicine ---

def test_list_natural_medicines(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/natural")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 10


def test_search_natural_medicines(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/natural?search=yarrow")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Yarrow"


def test_get_natural_medicine(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/natural/1")
    assert resp.status_code == 200
    assert resp.json()["name"] is not None


def test_create_natural_medicine(client: TestClient) -> None:
    resp = client.post("/api/natural", json={
        "name": "Lavender",
        "uses": "Calming, sleep aid, wound healing",
        "preparation": "Essential oil, tea from dried flowers",
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Lavender"


# --- Dosage Calculator ---

def test_calculate_dose_pediatric(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/dosage/calculate", json={
        "medication": "Acetaminophen",
        "weight_kg": 20.0,
        "age_months": 60,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_dose_mg"] == 300.0  # 20kg * 15mg/kg
    assert data["frequency_hours"] == 4


def test_calculate_dose_adult(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/dosage/calculate", json={
        "medication": "Acetaminophen",
        "weight_kg": 70.0,
        "age_months": 360,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_dose_mg"] == 650.0  # adult dose


def test_calculate_dose_max_cap(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/dosage/calculate", json={
        "medication": "Ibuprofen",
        "weight_kg": 100.0,
        "age_months": 180,
    })
    assert resp.status_code == 200
    data = resp.json()
    # 100kg * 10mg/kg = 1000mg, capped at max single 800mg
    assert data["recommended_dose_mg"] == 800.0


def test_calculate_dose_not_found(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/dosage/calculate", json={
        "medication": "NonexistentDrug",
        "weight_kg": 20.0,
        "age_months": 60,
    })
    assert resp.status_code == 404


def test_list_dosing_rules(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/dosage/rules")
    assert resp.status_code == 200
    assert len(resp.json()) >= 10


def test_list_dosing_rules_by_medication(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/dosage/rules?medication=Acetaminophen")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# --- Auth ---

def test_auth_rejected(client: TestClient) -> None:
    resp = client.get("/api/inventory/medications", headers={"X-User-Role": "viewer"})
    assert resp.status_code == 403
