"""Tests for epidemic surveillance module."""

import sqlite3

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path, get_connection

_TEST_CONFIG = {
    "database": {"path": ":memory:", "key": ""},
    "server": {"host": "0.0.0.0", "port": 8040},
    "surveillance": {
        "baseline_window_weeks": 4,
        "alert_thresholds": {"watch": 1.5, "warning": 2.0, "critical": 3.0},
    },
    "redis": {"url": "redis://localhost:6379"},
    "version": "0.1.0-test",
}


@pytest.fixture()
def client():
    """Set up in-memory database and test client."""
    set_db_path(":memory:")
    # Keep a connection alive so the shared in-memory DB persists
    anchor = get_connection()
    init_db()
    with patch("app.main.config", _TEST_CONFIG):
        from app.main import app
        yield TestClient(app)
    anchor.close()


# --- Health ---

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


# --- Surveillance ---

def test_list_syndromes(client):
    r = client.get("/api/surveillance/syndromes")
    assert r.status_code == 200
    assert "respiratory" in r.json()


def test_create_report(client):
    r = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
        "area": "zone-a",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["syndrome"] == "respiratory"
    assert data["area"] == "zone-a"


def test_create_report_invalid_syndrome(client):
    r = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "invalid",
        "age_group": "25-44",
        "sex": "male",
    })
    assert r.status_code == 400


def test_list_reports(client):
    client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    r = client.get("/api/surveillance/reports")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_get_report(client):
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    rid = cr.json()["id"]
    r = client.get(f"/api/surveillance/reports/{rid}")
    assert r.status_code == 200
    assert r.json()["id"] == rid


def test_update_report(client):
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    rid = cr.json()["id"]
    r = client.put(f"/api/surveillance/reports/{rid}", json={"notes": "updated"})
    assert r.status_code == 200
    assert r.json()["notes"] == "updated"


def test_delete_report(client):
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    rid = cr.json()["id"]
    r = client.delete(f"/api/surveillance/reports/{rid}")
    assert r.status_code == 204
    r2 = client.get(f"/api/surveillance/reports/{rid}")
    assert r2.status_code == 404


def test_counts(client):
    client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    r = client.get("/api/surveillance/counts")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_baseline(client):
    r = client.get("/api/surveillance/baseline?syndrome=respiratory")
    assert r.status_code == 200
    data = r.json()
    assert "daily_baseline" in data


# --- Alerts ---

def test_list_alerts(client):
    r = client.get("/api/alerts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_check_thresholds(client):
    r = client.post("/api/alerts/check")
    assert r.status_code == 200


def test_acknowledge_alert_not_found(client):
    r = client.post("/api/alerts/999/acknowledge")
    assert r.status_code == 404


# --- Contacts ---

def test_create_contact(client):
    # Create a case first
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    case_id = cr.json()["id"]

    r = client.post("/api/contacts", json={
        "case_id": case_id,
        "contact_person": "Jane Doe",
        "relationship": "coworker",
        "date_of_contact": "2026-02-28",
        "exposure_type": "close",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["contact_person"] == "Jane Doe"
    assert data["risk_score"] == 0.8


def test_create_contact_invalid_case(client):
    r = client.post("/api/contacts", json={
        "case_id": 999,
        "contact_person": "Jane Doe",
        "date_of_contact": "2026-02-28",
    })
    assert r.status_code == 400


def test_list_contacts(client):
    r = client.get("/api/contacts")
    assert r.status_code == 200


def test_update_contact(client):
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    case_id = cr.json()["id"]
    cc = client.post("/api/contacts", json={
        "case_id": case_id,
        "contact_person": "Jane Doe",
        "date_of_contact": "2026-02-28",
        "exposure_type": "casual",
    })
    cid = cc.json()["id"]
    r = client.put(f"/api/contacts/{cid}", json={"follow_up_status": "completed"})
    assert r.status_code == 200
    assert r.json()["follow_up_status"] == "completed"


def test_contact_network(client):
    cr = client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    case_id = cr.json()["id"]
    client.post("/api/contacts", json={
        "case_id": case_id,
        "contact_person": "Jane Doe",
        "date_of_contact": "2026-02-28",
        "exposure_type": "close",
    })
    r = client.get(f"/api/contacts/network/{case_id}")
    assert r.status_code == 200
    data = r.json()
    assert "direct_contacts" in data
    assert len(data["direct_contacts"]) == 1


# --- Quarantine ---

def test_create_quarantine(client):
    r = client.post("/api/quarantine", json={
        "person": "John Smith",
        "start_date": "2026-03-01",
        "expected_end": "2026-03-15",
        "location": "Building A Room 3",
        "reason": "Respiratory symptoms",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["person"] == "John Smith"
    assert data["status"] == "active"


def test_quarantine_census(client):
    client.post("/api/quarantine", json={
        "person": "John Smith",
        "start_date": "2026-03-01",
        "expected_end": "2026-03-15",
    })
    r = client.get("/api/quarantine/census")
    assert r.status_code == 200
    data = r.json()
    assert data["active"] == 1


def test_update_quarantine(client):
    cr = client.post("/api/quarantine", json={
        "person": "John Smith",
        "start_date": "2026-03-01",
        "expected_end": "2026-03-15",
    })
    qid = cr.json()["id"]
    r = client.put(f"/api/quarantine/{qid}", json={"status": "released"})
    assert r.status_code == 200
    assert r.json()["status"] == "released"


def test_quarantine_checkin(client):
    cr = client.post("/api/quarantine", json={
        "person": "John Smith",
        "start_date": "2026-03-01",
        "expected_end": "2026-03-15",
    })
    qid = cr.json()["id"]
    r = client.post(f"/api/quarantine/{qid}/checkins", json={
        "date": "2026-03-02",
        "temperature": 37.5,
        "symptoms": "mild cough",
    })
    assert r.status_code == 201
    assert r.json()["temperature"] == 37.5


def test_quarantine_supplies(client):
    cr = client.post("/api/quarantine", json={
        "person": "John Smith",
        "start_date": "2026-03-01",
        "expected_end": "2026-03-15",
    })
    qid = cr.json()["id"]
    r = client.post(f"/api/quarantine/{qid}/supplies", json={
        "item": "Water (2L bottles)",
        "quantity": 5,
    })
    assert r.status_code == 201
    assert r.json()["item"] == "Water (2L bottles)"

    # List supplies
    r2 = client.get(f"/api/quarantine/{qid}/supplies")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


# --- Timeline ---

def test_create_event(client):
    r = client.post("/api/timeline/events", json={
        "name": "Cholera outbreak 2025",
        "pathogen": "Vibrio cholerae",
        "start_date": "2025-06-01",
        "end_date": "2025-08-15",
        "total_cases": 150,
        "total_deaths": 5,
        "response_actions": "Water purification, oral rehydration",
        "lessons_learned": "Need better water testing supplies",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Cholera outbreak 2025"
    assert data["total_cases"] == 150


def test_list_events(client):
    client.post("/api/timeline/events", json={
        "name": "Test event",
        "start_date": "2025-01-01",
    })
    r = client.get("/api/timeline/events")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_update_event(client):
    cr = client.post("/api/timeline/events", json={
        "name": "Test event",
        "start_date": "2025-01-01",
    })
    eid = cr.json()["id"]
    r = client.put(f"/api/timeline/events/{eid}", json={"total_cases": 42})
    assert r.status_code == 200
    assert r.json()["total_cases"] == 42


def test_delete_event(client):
    cr = client.post("/api/timeline/events", json={
        "name": "Test event",
        "start_date": "2025-01-01",
    })
    eid = cr.json()["id"]
    r = client.delete(f"/api/timeline/events/{eid}")
    assert r.status_code == 204


def test_compare_with_history(client):
    r = client.get("/api/timeline/compare?syndrome=respiratory")
    assert r.status_code == 200
    assert "current_trend" in r.json()


# --- Sharing ---

def test_export_anonymized(client):
    client.post("/api/surveillance/reports", json={
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "sex": "male",
    })
    r = client.get("/api/sharing/export")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    # Verify no PII - only aggregated fields
    for rec in data:
        assert "patient_id" not in rec
        assert "notes" not in rec


def test_receive_community_data(client):
    r = client.post("/api/sharing/receive", json=[{
        "community_id": "community-alpha",
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "count": 5,
    }])
    assert r.status_code == 201
    assert r.json()["ingested"] == 1


def test_list_communities(client):
    client.post("/api/sharing/receive", json=[{
        "community_id": "community-alpha",
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "count": 5,
    }])
    r = client.get("/api/sharing/communities")
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert r.json()[0]["community_id"] == "community-alpha"


def test_compare_communities(client):
    client.post("/api/sharing/receive", json=[{
        "community_id": "community-alpha",
        "date": "2026-03-01",
        "syndrome": "respiratory",
        "age_group": "25-44",
        "count": 5,
    }])
    r = client.get("/api/sharing/comparison?syndrome=respiratory")
    assert r.status_code == 200
    assert len(r.json()) >= 1
