"""Tests for the backup FastAPI endpoints."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from shared.db import connect, execute

# Patch config before importing app
_TEST_CONFIG = {
    "modules": {},
    "status_db": ":memory:",
    "snapshot_dir": "/tmp/test-snapshots",
    "blob_dir": "/tmp/test-blobs",
    "usb_mount": "/tmp/test-usb",
}


@pytest.fixture()
def client(tmp_path):
    """Create a test client with temporary config."""
    test_config = {
        **_TEST_CONFIG,
        "status_db": str(tmp_path / "status.db"),
        "snapshot_dir": str(tmp_path / "snapshots"),
        "blob_dir": str(tmp_path / "blobs"),
    }

    import app.main as main_mod
    main_mod.config = test_config
    main_mod._status_conn = None  # Reset connection

    return TestClient(main_mod.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_snapshot_no_modules(client):
    resp = client.post("/api/backup/snapshot")
    assert resp.status_code == 400


def test_snapshot_with_modules(client, tmp_path):
    # Create a test database
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    conn.execute("CREATE TABLE t (id INTEGER)")
    conn.commit()
    conn.close()

    import app.main as main_mod
    main_mod.config["modules"] = {"testmod": {"db_path": db_path}}
    main_mod.config["snapshot_dir"] = str(tmp_path / "snaps")

    resp = client.post("/api/backup/snapshot")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["snapshots"]) == 1
    assert data["snapshots"][0]["module"] == "testmod"


def test_status(client):
    resp = client.get("/api/backup/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "backups" in data
    assert "drive" in data


def test_history(client):
    resp = client.get("/api/backup/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_verify_missing_path(client):
    resp = client.post("/api/backup/verify", json={})
    assert resp.status_code == 400


def test_restore_missing_path(client):
    resp = client.post("/api/backup/restore", json={})
    assert resp.status_code == 400


def test_paper_endpoint(client):
    sections = [
        {
            "heading": "Test",
            "headers": ["A", "B"],
            "rows": [["1", "2"]],
        }
    ]
    resp = client.post("/api/backup/paper", json={"title": "Test Backup", "sections": sections})
    assert resp.status_code == 200
    assert "<!DOCTYPE html>" in resp.text
    assert "Test" in resp.text
