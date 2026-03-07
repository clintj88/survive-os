"""Tests for the Meshtastic Gateway API."""

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
    """Client with sample messages and radios."""
    execute(
        """INSERT INTO messages (sender, recipient, content, timestamp, channel, mesh_id, direction)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("!abc123", "^all", "Hello mesh", "2026-03-07T10:00:00Z", 0, "msg001", "rx"),
    )
    execute(
        """INSERT INTO messages (sender, recipient, content, timestamp, channel, mesh_id, direction)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("local", "^all", "Reply from gateway", "2026-03-07T10:01:00Z", 0, "", "tx"),
    )
    execute(
        """INSERT INTO radios (node_id, long_name, short_name, hw_model, battery_level, snr)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("!abc123", "Alpha Node", "ALF", "HELTEC_V3", 85, 7.5),
    )
    execute(
        """INSERT INTO radios (node_id, long_name, short_name, hw_model, battery_level, snr)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("!def456", "Bravo Node", "BRV", "TBEAM", 42, 3.2),
    )
    return client


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "radio_connected" in data


def test_list_messages_empty(client: TestClient) -> None:
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_messages(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2


def test_list_messages_by_channel(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/messages?channel=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = seeded_client.get("/api/messages?channel=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_messages_with_limit(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/messages?limit=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_send_message(client: TestClient) -> None:
    resp = client.post("/api/messages", json={
        "content": "Test message",
        "recipient": "^all",
        "channel": 0,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Test message"
    assert data["recipient"] == "^all"


def test_get_status(client: TestClient) -> None:
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "radio_connected" in data
    assert "message_count" in data
    assert "node_count" in data


def test_list_radios_empty(client: TestClient) -> None:
    resp = client.get("/api/provisioning/radios")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_radios(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/provisioning/radios")
    assert resp.status_code == 200
    radios = resp.json()
    assert len(radios) == 2
    assert radios[0]["node_id"] in ("!abc123", "!def456")


def test_assign_radio(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/provisioning/radios/assign", json={
        "node_id": "!abc123",
        "user": "john",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_user"] == "john"


def test_assign_radio_not_found(client: TestClient) -> None:
    resp = client.post("/api/provisioning/radios/assign", json={
        "node_id": "!nonexistent",
        "user": "john",
    })
    assert resp.status_code == 404


def test_get_topology(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/provisioning/topology")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert len(data["nodes"]) == 2


def test_list_channels_empty(client: TestClient) -> None:
    resp = client.get("/api/provisioning/channels")
    assert resp.status_code == 200
    assert resp.json() == []
