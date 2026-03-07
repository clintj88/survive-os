"""Tests for the Ham Radio API."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    """Set up a fresh database for each test."""
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    from app.main import app
    return TestClient(app)


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# --- Frequencies ---

def test_list_frequencies_empty(client: TestClient) -> None:
    resp = client.get("/api/frequencies")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_frequency(client: TestClient) -> None:
    resp = client.post("/api/frequencies", json={
        "freq_mhz": 146.52,
        "name": "2m National Simplex",
        "band": "2m",
        "mode": "FM",
        "usage": "simplex",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["freq_mhz"] == 146.52
    assert data["name"] == "2m National Simplex"


def test_get_frequency(client: TestClient) -> None:
    client.post("/api/frequencies", json={
        "freq_mhz": 7.24, "name": "40m Emergency", "band": "40m", "mode": "SSB",
    })
    resp = client.get("/api/frequencies/1")
    assert resp.status_code == 200
    assert resp.json()["freq_mhz"] == 7.24


def test_get_frequency_not_found(client: TestClient) -> None:
    resp = client.get("/api/frequencies/999")
    assert resp.status_code == 404


def test_update_frequency(client: TestClient) -> None:
    client.post("/api/frequencies", json={
        "freq_mhz": 14.3, "name": "20m Net", "band": "20m", "mode": "SSB",
    })
    resp = client.put("/api/frequencies/1", json={"name": "20m Emergency Net"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "20m Emergency Net"


def test_delete_frequency(client: TestClient) -> None:
    client.post("/api/frequencies", json={
        "freq_mhz": 446.0, "name": "70cm Simplex", "band": "70cm", "mode": "FM",
    })
    resp = client.delete("/api/frequencies/1")
    assert resp.status_code == 204
    resp = client.get("/api/frequencies/1")
    assert resp.status_code == 404


def test_filter_frequencies_by_band(client: TestClient) -> None:
    client.post("/api/frequencies", json={
        "freq_mhz": 146.52, "name": "2m Simplex", "band": "2m", "mode": "FM",
    })
    client.post("/api/frequencies", json={
        "freq_mhz": 446.0, "name": "70cm Simplex", "band": "70cm", "mode": "FM",
    })
    resp = client.get("/api/frequencies?band=2m")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["band"] == "2m"


# --- Scheduled Contacts ---

def test_list_contacts_empty(client: TestClient) -> None:
    resp = client.get("/api/contacts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_contact(client: TestClient) -> None:
    resp = client.post("/api/contacts", json={
        "title": "Morning Net",
        "callsign": "W1AW",
        "freq_mhz": 14.3,
        "mode": "SSB",
        "scheduled_at": "2026-03-08T08:00:00",
        "duration_minutes": 60,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Morning Net"
    assert data["callsign"] == "W1AW"


def test_get_contact(client: TestClient) -> None:
    client.post("/api/contacts", json={
        "title": "Evening Sked",
        "scheduled_at": "2026-03-08T20:00:00",
    })
    resp = client.get("/api/contacts/1")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Evening Sked"


def test_get_contact_not_found(client: TestClient) -> None:
    resp = client.get("/api/contacts/999")
    assert resp.status_code == 404


def test_update_contact(client: TestClient) -> None:
    client.post("/api/contacts", json={
        "title": "Net", "scheduled_at": "2026-03-08T08:00:00",
    })
    resp = client.put("/api/contacts/1", json={"title": "Updated Net"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Net"


def test_delete_contact(client: TestClient) -> None:
    client.post("/api/contacts", json={
        "title": "Delete Me", "scheduled_at": "2026-03-08T08:00:00",
    })
    resp = client.delete("/api/contacts/1")
    assert resp.status_code == 204
    resp = client.get("/api/contacts/1")
    assert resp.status_code == 404


# --- Winlink ---

def test_list_winlink_empty(client: TestClient) -> None:
    resp = client.get("/api/winlink/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_compose_winlink(client: TestClient) -> None:
    resp = client.post("/api/winlink/compose", json={
        "to": "W1AW",
        "subject": "Test Message",
        "body": "Hello from SURVIVE OS",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["to_addr"] == "W1AW"
    assert data["status"] == "queued"
    assert data["direction"] == "outbound"


def test_get_winlink_message(client: TestClient) -> None:
    client.post("/api/winlink/compose", json={
        "to": "W1AW", "subject": "Test", "body": "Body",
    })
    resp = client.get("/api/winlink/messages/1")
    assert resp.status_code == 200
    assert resp.json()["subject"] == "Test"


def test_get_winlink_message_not_found(client: TestClient) -> None:
    resp = client.get("/api/winlink/messages/999")
    assert resp.status_code == 404


def test_filter_winlink_by_direction(client: TestClient) -> None:
    client.post("/api/winlink/compose", json={
        "to": "W1AW", "subject": "Out", "body": "Body",
    })
    resp = client.get("/api/winlink/messages?direction=outbound")
    assert len(resp.json()) == 1
    resp = client.get("/api/winlink/messages?direction=inbound")
    assert len(resp.json()) == 0


# --- JS8Call ---

def test_js8call_status(client: TestClient) -> None:
    resp = client.get("/api/js8call/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "connected" in data


def test_js8call_messages_empty(client: TestClient) -> None:
    resp = client.get("/api/js8call/messages")
    assert resp.status_code == 200
    assert resp.json() == []
