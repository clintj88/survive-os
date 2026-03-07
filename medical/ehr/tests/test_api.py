"""Tests for the EHR-Lite API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


HEADERS = {"X-User": "dr.test", "X-Role": "medical"}


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test_ehr.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def patient_client(client: TestClient) -> TestClient:
    """Client with a patient created."""
    execute(
        """INSERT INTO patients
           (patient_id, first_name, last_name, date_of_birth, sex, blood_type, allergies, chronic_conditions, emergency_contact)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("P-TEST0001", "Jane", "Doe", "1985-03-15", "F", "O+",
         '["Penicillin","Sulfa"]', '["Asthma","Hypertension"]', "John Doe 555-1234"),
    )
    return client


@pytest.fixture
def visit_client(patient_client: TestClient) -> TestClient:
    """Client with a patient and visit."""
    execute(
        """INSERT INTO visits (patient_id, provider, visit_date, subjective, objective, assessment, plan, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (1, "Dr. Smith", "2026-03-01", "Headache for 3 days", "Alert, oriented",
         "Tension headache", "Ibuprofen 400mg q6h PRN", "Follow up in 1 week"),
    )
    return patient_client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Auth ---

def test_auth_required(client: TestClient) -> None:
    resp = client.get("/api/patients", headers={"X-User": "", "X-Role": "medical"})
    assert resp.status_code == 401


def test_auth_wrong_role(client: TestClient) -> None:
    resp = client.get("/api/patients", headers={"X-User": "someone", "X-Role": "viewer"})
    assert resp.status_code == 403


# --- Patients ---

def test_create_patient(client: TestClient) -> None:
    resp = client.post("/api/patients", json={
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "1990-01-01",
        "sex": "M",
        "blood_type": "A+",
        "allergies": ["Latex"],
        "chronic_conditions": ["Diabetes"],
        "emergency_contact": "Jane Smith 555-0000",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "John"
    assert data["patient_id"].startswith("P-")
    assert data["allergies"] == ["Latex"]


def test_list_patients(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients", headers=HEADERS)
    assert resp.status_code == 200
    patients = resp.json()
    assert len(patients) == 1
    assert patients[0]["last_name"] == "Doe"


def test_search_patients_by_name(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients?name=Jane", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = patient_client.get("/api/patients?name=Nobody", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_search_patients_by_blood_type(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients?blood_type=O%2B", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_patients_by_condition(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients?condition=Asthma", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_patient(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients/1", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["allergies"] == ["Penicillin", "Sulfa"]


def test_get_patient_not_found(client: TestClient) -> None:
    resp = client.get("/api/patients/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_patient(patient_client: TestClient) -> None:
    resp = patient_client.put("/api/patients/1", json={
        "notes": "Updated notes",
        "allergies": ["Penicillin", "Sulfa", "Codeine"],
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["notes"] == "Updated notes"
    assert "Codeine" in data["allergies"]


def test_delete_patient(patient_client: TestClient) -> None:
    resp = patient_client.delete("/api/patients/1", headers=HEADERS)
    assert resp.status_code == 204

    resp = patient_client.get("/api/patients/1", headers=HEADERS)
    assert resp.status_code == 404


# --- Visits ---

def test_create_visit(patient_client: TestClient) -> None:
    resp = patient_client.post("/api/patients/1/visits", json={
        "provider": "Dr. Adams",
        "subjective": "Cough for 1 week",
        "objective": "Lungs clear bilateral",
        "assessment": "Viral URI",
        "plan": "Rest, fluids, follow up PRN",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["provider"] == "Dr. Adams"
    assert data["assessment"] == "Viral URI"


def test_list_visits(visit_client: TestClient) -> None:
    resp = visit_client.get("/api/patients/1/visits", headers=HEADERS)
    assert resp.status_code == 200
    visits = resp.json()
    assert len(visits) == 1
    assert visits[0]["provider"] == "Dr. Smith"


def test_get_visit(visit_client: TestClient) -> None:
    resp = visit_client.get("/api/patients/1/visits/1", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["subjective"] == "Headache for 3 days"


def test_update_visit(visit_client: TestClient) -> None:
    resp = visit_client.put("/api/patients/1/visits/1", json={
        "plan": "Updated plan: add rest",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["plan"] == "Updated plan: add rest"


def test_visit_patient_not_found(client: TestClient) -> None:
    resp = client.get("/api/patients/999/visits", headers=HEADERS)
    assert resp.status_code == 404


# --- Vitals ---

def test_create_vitals(patient_client: TestClient) -> None:
    resp = patient_client.post("/api/patients/1/vitals", json={
        "temperature": 37.2,
        "pulse": 72,
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "respiration_rate": 16,
        "spo2": 98.0,
        "weight": 65.5,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["temperature"] == 37.2
    assert data["pulse"] == 72


def test_list_vitals(patient_client: TestClient) -> None:
    execute(
        """INSERT INTO vitals (patient_id, temperature, pulse, bp_systolic, bp_diastolic, spo2)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 37.0, 70, 118, 78, 97.0),
    )
    resp = patient_client.get("/api/patients/1/vitals", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_vital_trends(patient_client: TestClient) -> None:
    for temp in [37.0, 37.5, 38.0]:
        execute(
            "INSERT INTO vitals (patient_id, temperature) VALUES (?, ?)",
            (1, temp),
        )
    resp = patient_client.get("/api/patients/1/vitals/trends/temperature", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


def test_vital_trends_invalid_sign(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients/1/vitals/trends/invalid", headers=HEADERS)
    assert resp.status_code == 400


def test_vital_alerts(patient_client: TestClient) -> None:
    execute(
        """INSERT INTO vitals (patient_id, temperature, pulse, spo2)
           VALUES (?, ?, ?, ?)""",
        (1, 39.5, 110, 88.0),
    )
    resp = patient_client.get("/api/patients/1/vitals/alerts", headers=HEADERS)
    assert resp.status_code == 200
    alerts = resp.json()
    signs = {a["sign"] for a in alerts}
    assert "temperature" in signs
    assert "pulse" in signs
    assert "spo2" in signs


def test_vital_alerts_no_vitals(patient_client: TestClient) -> None:
    resp = patient_client.get("/api/patients/1/vitals/alerts", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


# --- Wounds ---

def test_create_wound(patient_client: TestClient) -> None:
    resp = patient_client.post("/api/patients/1/wounds", json={
        "body_location": "Left forearm",
        "wound_type": "laceration",
        "size": "3cm x 1cm",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["body_location"] == "Left forearm"
    assert data["status"] == "open"


def test_list_wounds(patient_client: TestClient) -> None:
    execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type, size) VALUES (?, ?, ?, ?)",
        (1, "Right hand", "burn", "2cm x 2cm"),
    )
    resp = patient_client.get("/api/patients/1/wounds", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_wound_with_entries(patient_client: TestClient) -> None:
    execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type) VALUES (?, ?, ?)",
        (1, "Left leg", "puncture"),
    )
    execute(
        "INSERT INTO wound_entries (wound_id, treatment_notes, healing_status) VALUES (?, ?, ?)",
        (1, "Cleaned and dressed", "ongoing"),
    )
    resp = patient_client.get("/api/patients/1/wounds/1", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["treatment_notes"] == "Cleaned and dressed"


def test_update_wound_status(patient_client: TestClient) -> None:
    execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type) VALUES (?, ?, ?)",
        (1, "Left leg", "puncture"),
    )
    resp = patient_client.put("/api/patients/1/wounds/1", json={
        "status": "healed",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "healed"


def test_add_wound_entry(patient_client: TestClient) -> None:
    execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type) VALUES (?, ?, ?)",
        (1, "Left arm", "laceration"),
    )
    resp = patient_client.post("/api/patients/1/wounds/1/entries", json={
        "treatment_notes": "Changed dressing, wound looks good",
        "healing_status": "improving",
    }, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["healing_status"] == "improving"


def test_list_wound_entries(patient_client: TestClient) -> None:
    execute(
        "INSERT INTO wounds (patient_id, body_location, wound_type) VALUES (?, ?, ?)",
        (1, "Left arm", "laceration"),
    )
    execute(
        "INSERT INTO wound_entries (wound_id, treatment_notes) VALUES (?, ?)",
        (1, "Entry 1"),
    )
    execute(
        "INSERT INTO wound_entries (wound_id, treatment_notes) VALUES (?, ?)",
        (1, "Entry 2"),
    )
    resp = patient_client.get("/api/patients/1/wounds/1/entries", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- Vaccinations ---

def test_create_vaccination(patient_client: TestClient) -> None:
    resp = patient_client.post("/api/patients/1/vaccinations", json={
        "vaccine_name": "Tetanus/Diphtheria (Td)",
        "date_administered": "2026-03-01",
        "lot_number": "TD-2026-001",
        "site": "Left deltoid",
        "administered_by": "Nurse Johnson",
        "next_dose_due": "2036-03-01",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["vaccine_name"] == "Tetanus/Diphtheria (Td)"
    assert data["next_dose_due"] == "2036-03-01"


def test_list_vaccinations(patient_client: TestClient) -> None:
    execute(
        """INSERT INTO vaccinations (patient_id, vaccine_name, date_administered, administered_by)
           VALUES (?, ?, ?, ?)""",
        (1, "Hepatitis B", "2026-01-15", "Dr. Smith"),
    )
    resp = patient_client.get("/api/patients/1/vaccinations", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_overdue_vaccinations(patient_client: TestClient) -> None:
    execute(
        """INSERT INTO vaccinations (patient_id, vaccine_name, date_administered, next_dose_due)
           VALUES (?, ?, ?, ?)""",
        (1, "Tetanus", "2015-01-01", "2025-01-01"),
    )
    resp = patient_client.get("/api/patients/1/vaccinations/overdue", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_vaccine_schedules(client: TestClient) -> None:
    resp = client.get("/api/vaccinations/schedules", headers=HEADERS)
    assert resp.status_code == 200
    schedules = resp.json()
    assert "Tetanus/Diphtheria (Td)" in schedules
    assert "Measles/MMR" in schedules


def test_vaccination_coverage(patient_client: TestClient) -> None:
    execute(
        """INSERT INTO vaccinations (patient_id, vaccine_name, date_administered)
           VALUES (?, ?, ?)""",
        (1, "Hepatitis B", "2026-01-15"),
    )
    resp = patient_client.get("/api/vaccinations/coverage", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["patients_vaccinated"] == 1


# --- Summary ---

def test_patient_summary(visit_client: TestClient) -> None:
    # Add vitals and vaccination
    execute(
        "INSERT INTO vitals (patient_id, temperature, pulse, bp_systolic, bp_diastolic) VALUES (?, ?, ?, ?, ?)",
        (1, 37.0, 72, 120, 80),
    )
    execute(
        "INSERT INTO vaccinations (patient_id, vaccine_name, date_administered) VALUES (?, ?, ?)",
        (1, "Tetanus", "2026-01-01"),
    )
    resp = visit_client.get("/api/patients/1/summary", headers=HEADERS)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "Jane" in body
    assert "Doe" in body
    assert "Penicillin" in body
    assert "Dr. Smith" in body
    assert "Tetanus" in body


def test_patient_summary_not_found(client: TestClient) -> None:
    resp = client.get("/api/patients/999/summary", headers=HEADERS)
    assert resp.status_code == 404


# --- Audit Log ---

def test_audit_log_recorded(patient_client: TestClient) -> None:
    # Access patient to generate audit entries
    patient_client.get("/api/patients/1", headers=HEADERS)
    rows = query("SELECT * FROM audit_log WHERE resource_type = 'patient'")
    assert len(rows) >= 1
    assert rows[0]["user_name"] == "dr.test"
