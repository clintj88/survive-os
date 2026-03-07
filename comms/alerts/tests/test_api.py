"""Tests for the Alerts API."""

from pathlib import Path
from unittest.mock import patch

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


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with an alert already created."""
    with patch("app.routes.broadcast_alert", return_value=[
        {"alert_id": 1, "channel": "comms.alerts", "status": "local_only"},
    ]):
        client.post("/api/alerts", json={
            "title": "Test Alert",
            "message": "This is a test alert.",
            "severity": "warning",
            "author": "admin",
        })
    return client


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_create_alert(client: TestClient) -> None:
    with patch("app.routes.broadcast_alert", return_value=[
        {"alert_id": 1, "channel": "comms.alerts", "status": "local_only"},
    ]):
        resp = client.post("/api/alerts", json={
            "title": "Fire Warning",
            "message": "Wildfire detected near sector 7.",
            "severity": "critical",
            "author": "admin",
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Fire Warning"
    assert data["severity"] == "critical"
    assert data["active"] == 1


def test_create_alert_invalid_severity(client: TestClient) -> None:
    resp = client.post("/api/alerts", json={
        "title": "Bad",
        "message": "test",
        "severity": "invalid",
        "author": "admin",
    })
    assert resp.status_code == 400


def test_list_alerts(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 1
    assert alerts[0]["title"] == "Test Alert"


def test_list_alerts_filter_active(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/alerts?active=true")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = seeded_client.get("/api/alerts?active=false")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_list_alerts_filter_severity(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/alerts?severity=warning")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = seeded_client.get("/api/alerts?severity=emergency")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_alert(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/alerts/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Alert"
    assert "acknowledgments" in data
    assert "broadcasts" in data


def test_get_alert_not_found(client: TestClient) -> None:
    resp = client.get("/api/alerts/999")
    assert resp.status_code == 404


def test_resolve_alert(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/alerts/1/resolve", json={
        "resolved_by": "admin",
    })
    assert resp.status_code == 200
    assert resp.json()["active"] == 0
    assert resp.json()["resolved_by"] == "admin"


def test_resolve_already_resolved(seeded_client: TestClient) -> None:
    seeded_client.post("/api/alerts/1/resolve", json={"resolved_by": "admin"})
    resp = seeded_client.post("/api/alerts/1/resolve", json={"resolved_by": "admin"})
    assert resp.status_code == 400


def test_resolve_not_found(client: TestClient) -> None:
    resp = client.post("/api/alerts/999/resolve", json={"resolved_by": "admin"})
    assert resp.status_code == 404


def test_acknowledge_alert(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/alerts/1/ack", json={
        "user_id": "alice",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "acknowledged"


def test_acknowledge_duplicate(seeded_client: TestClient) -> None:
    seeded_client.post("/api/alerts/1/ack", json={"user_id": "alice"})
    resp = seeded_client.post("/api/alerts/1/ack", json={"user_id": "alice"})
    assert resp.status_code == 409


def test_acknowledge_not_found(client: TestClient) -> None:
    resp = client.post("/api/alerts/999/ack", json={"user_id": "alice"})
    assert resp.status_code == 404


def test_list_acknowledgments(seeded_client: TestClient) -> None:
    seeded_client.post("/api/alerts/1/ack", json={"user_id": "alice"})
    seeded_client.post("/api/alerts/1/ack", json={"user_id": "bob"})
    resp = seeded_client.get("/api/alerts/1/acks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_acknowledgments_not_found(client: TestClient) -> None:
    resp = client.get("/api/alerts/999/acks")
    assert resp.status_code == 404
