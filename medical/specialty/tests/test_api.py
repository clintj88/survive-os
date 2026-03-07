"""Tests for the Medical Specialty API."""

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


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Auth ---

def test_auth_rejects_wrong_role(client: TestClient) -> None:
    resp = client.get("/api/prenatal/patients", headers={"X-User-Role": "guest"})
    assert resp.status_code == 403


# --- Prenatal ---

def test_prenatal_crud(client: TestClient) -> None:
    # Create patient
    resp = client.post("/api/prenatal/patients", json={
        "patient_id": "P001",
        "estimated_due_date": "2026-09-15",
        "gravida": 2,
        "para": 1,
        "risk_factors": ["age_over_35"],
        "blood_type": "A",
        "rh_factor": "positive",
    })
    assert resp.status_code == 201
    patient = resp.json()
    pid = patient["id"]
    assert patient["patient_id"] == "P001"

    # List patients
    resp = client.get("/api/prenatal/patients")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Get patient
    resp = client.get(f"/api/prenatal/patients/{pid}")
    assert resp.status_code == 200

    # Update patient
    resp = client.put(f"/api/prenatal/patients/{pid}", json={"gravida": 3})
    assert resp.status_code == 200
    assert resp.json()["gravida"] == 3

    # Get visit schedule
    resp = client.get(f"/api/prenatal/patients/{pid}/schedule")
    assert resp.status_code == 200
    schedule = resp.json()["schedule"]
    assert len(schedule) == 14  # standard visit weeks


def test_prenatal_visit(client: TestClient) -> None:
    client.post("/api/prenatal/patients", json={
        "patient_id": "P002",
        "estimated_due_date": "2026-09-15",
    })
    resp = client.post("/api/prenatal/patients/1/visits", json={
        "visit_date": "2026-03-01",
        "week_number": 12,
        "fundal_height": 12.5,
        "fetal_heart_rate": 155,
        "maternal_weight": 68.0,
        "provider": "Dr. Smith",
    })
    assert resp.status_code == 201
    assert resp.json()["week_number"] == 12

    resp = client.get("/api/prenatal/patients/1/visits")
    assert len(resp.json()) == 1


def test_prenatal_delivery(client: TestClient) -> None:
    client.post("/api/prenatal/patients", json={
        "patient_id": "P003",
        "estimated_due_date": "2026-03-01",
    })
    resp = client.post("/api/prenatal/patients/1/deliveries", json={
        "delivery_date": "2026-03-02",
        "delivery_type": "vaginal",
        "birth_weight": 3.4,
        "apgar_1min": 8,
        "apgar_5min": 9,
        "provider": "Dr. Smith",
    })
    assert resp.status_code == 201
    assert resp.json()["delivery_type"] == "vaginal"


def test_prenatal_postpartum(client: TestClient) -> None:
    client.post("/api/prenatal/patients", json={
        "patient_id": "P004",
        "estimated_due_date": "2026-03-01",
    })
    resp = client.post("/api/prenatal/patients/1/postpartum", json={
        "scheduled_date": "2026-03-02",
        "followup_type": "1 day",
    })
    assert resp.status_code == 201

    resp = client.get("/api/prenatal/patients/1/postpartum")
    assert len(resp.json()) == 1


def test_prenatal_not_found(client: TestClient) -> None:
    resp = client.get("/api/prenatal/patients/999")
    assert resp.status_code == 404


def test_prenatal_reference_data(client: TestClient) -> None:
    resp = client.get("/api/prenatal/risk-factors")
    assert resp.status_code == 200
    assert "age_over_35" in resp.json()

    resp = client.get("/api/prenatal/visit-weeks")
    assert resp.status_code == 200
    assert 40 in resp.json()


# --- Dental ---

def test_dental_crud(client: TestClient) -> None:
    # Create patient
    resp = client.post("/api/dental/patients", json={"patient_id": "D001"})
    assert resp.status_code == 201
    pid = resp.json()["id"]

    # Get chart (defaults to healthy)
    resp = client.get(f"/api/dental/patients/{pid}/chart")
    assert resp.status_code == 200
    chart = resp.json()
    assert len(chart["teeth"]) == 32
    assert chart["teeth"][0]["status"] == "healthy"

    # Update tooth
    resp = client.put(f"/api/dental/patients/{pid}/chart/5", json={
        "status": "cavity",
        "notes": "Small cavity detected",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "cavity"

    # Verify chart updated
    resp = client.get(f"/api/dental/patients/{pid}/chart")
    tooth_5 = [t for t in resp.json()["teeth"] if t["tooth_number"] == 5][0]
    assert tooth_5["status"] == "cavity"


def test_dental_pediatric(client: TestClient) -> None:
    resp = client.post("/api/dental/patients", json={
        "patient_id": "D002",
        "is_pediatric": True,
    })
    assert resp.status_code == 201
    pid = resp.json()["id"]

    resp = client.get(f"/api/dental/patients/{pid}/chart")
    assert len(resp.json()["teeth"]) == 20


def test_dental_invalid_status(client: TestClient) -> None:
    client.post("/api/dental/patients", json={"patient_id": "D003"})
    resp = client.put("/api/dental/patients/1/chart/1", json={"status": "invalid"})
    assert resp.status_code == 400


def test_dental_invalid_tooth(client: TestClient) -> None:
    client.post("/api/dental/patients", json={"patient_id": "D004"})
    resp = client.put("/api/dental/patients/1/chart/33", json={"status": "healthy"})
    assert resp.status_code == 400


def test_dental_treatment(client: TestClient) -> None:
    client.post("/api/dental/patients", json={"patient_id": "D005"})
    resp = client.post("/api/dental/patients/1/treatments", json={
        "tooth_number": 14,
        "procedure_type": "filling",
        "provider": "Dr. Jones",
    })
    assert resp.status_code == 201

    resp = client.get("/api/dental/patients/1/treatments")
    assert len(resp.json()) == 1


def test_dental_preventive(client: TestClient) -> None:
    client.post("/api/dental/patients", json={"patient_id": "D006"})
    resp = client.post("/api/dental/patients/1/preventive", json={
        "last_cleaning": "2026-01-15",
        "next_cleaning": "2026-07-15",
    })
    assert resp.status_code == 201

    resp = client.get("/api/dental/patients/1/preventive")
    assert resp.json()["last_cleaning"] == "2026-01-15"


def test_dental_emergency_protocols(client: TestClient) -> None:
    resp = client.get("/api/dental/emergency-protocols")
    assert resp.status_code == 200
    protocols = resp.json()
    assert len(protocols) == 4
    assert protocols[0]["condition"] == "Knocked-out tooth"


# --- Mental Health ---

def test_mental_checkin(client: TestClient) -> None:
    resp = client.post("/api/mental/checkins", json={
        "patient_id": "M001",
        "mood": 4,
        "sleep_quality": 3,
        "appetite": 4,
        "energy": 3,
        "anxiety_level": 2,
        "notes": "Feeling okay today",
    })
    assert resp.status_code == 201
    checkin = resp.json()
    assert checkin["mood"] == 4

    resp = client.get("/api/mental/checkins/M001")
    assert len(resp.json()) == 1


def test_mental_checkin_validation(client: TestClient) -> None:
    resp = client.post("/api/mental/checkins", json={
        "patient_id": "M002",
        "mood": 6,  # out of range
        "sleep_quality": 3,
        "appetite": 3,
        "energy": 3,
        "anxiety_level": 3,
    })
    assert resp.status_code == 422


def test_mental_trends(client: TestClient) -> None:
    # Create multiple check-ins
    for mood in [3, 4, 5]:
        client.post("/api/mental/checkins", json={
            "patient_id": "M003",
            "mood": mood,
            "sleep_quality": 3,
            "appetite": 3,
            "energy": 3,
            "anxiety_level": 2,
        })

    resp = client.get("/api/mental/checkins/M003/trends?days=30")
    assert resp.status_code == 200
    trends = resp.json()
    assert len(trends["data"]) == 3
    assert trends["averages"]["mood"] == 4.0


def test_mental_delete_checkin(client: TestClient) -> None:
    resp = client.post("/api/mental/checkins", json={
        "patient_id": "M004",
        "mood": 3,
        "sleep_quality": 3,
        "appetite": 3,
        "energy": 3,
        "anxiety_level": 3,
    })
    checkin_id = resp.json()["id"]

    resp = client.delete(f"/api/mental/checkins/{checkin_id}?patient_id=M004")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    resp = client.get("/api/mental/checkins/M004")
    assert len(resp.json()) == 0


def test_mental_provider_notes_require_consent(client: TestClient) -> None:
    resp = client.post("/api/mental/notes", json={
        "patient_id": "M005",
        "provider": "Dr. Lee",
        "note": "Patient doing well",
        "patient_consent": False,
    })
    assert resp.status_code == 400

    resp = client.post("/api/mental/notes", json={
        "patient_id": "M005",
        "provider": "Dr. Lee",
        "note": "Patient doing well",
        "patient_consent": True,
    })
    assert resp.status_code == 201

    resp = client.get("/api/mental/notes/M005")
    assert len(resp.json()) == 1


def test_mental_resources(client: TestClient) -> None:
    resp = client.get("/api/mental/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["coping_strategies"]) > 0
    assert len(data["self_care_tips"]) > 0
    assert len(data["crisis_info"]) > 0


# --- Veterinary ---

def test_vet_visit(client: TestClient) -> None:
    resp = client.post("/api/vet/visits", json={
        "animal_id": "COW-001",
        "condition": "Bloat",
        "treatment": "Anti-foaming agent administered",
        "provider": "Dr. Vet",
    })
    assert resp.status_code == 201
    assert resp.json()["animal_id"] == "COW-001"

    resp = client.get("/api/vet/visits?animal_id=COW-001")
    assert len(resp.json()) == 1

    resp = client.get("/api/vet/visits")
    assert len(resp.json()) == 1


def test_vet_herd_health(client: TestClient) -> None:
    client.post("/api/vet/visits", json={
        "animal_id": "COW-001",
        "condition": "Bloat",
    })
    client.post("/api/vet/visits", json={
        "animal_id": "COW-002",
        "condition": "Mastitis",
    })
    client.post("/api/vet/visits", json={
        "animal_id": "COW-001",
        "condition": "Foot Rot",
    })

    resp = client.get("/api/vet/herd-health")
    assert resp.status_code == 200
    report = resp.json()
    assert report["total_visits"] == 3
    assert report["unique_animals"] == 2


def test_vet_conditions(client: TestClient) -> None:
    resp = client.get("/api/vet/conditions")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_vet_protocols(client: TestClient) -> None:
    resp = client.get("/api/vet/protocols")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_vet_animal_info(client: TestClient) -> None:
    client.post("/api/vet/visits", json={
        "animal_id": "COW-005",
        "condition": "Respiratory Infection",
    })
    resp = client.get("/api/vet/animals/COW-005")
    assert resp.status_code == 200
    data = resp.json()
    assert data["animal_id"] == "COW-005"
    assert len(data["vet_visits"]) == 1
