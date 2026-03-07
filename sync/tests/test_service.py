"""Tests for the sync FastAPI service."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_config = {
            "database": {"path": str(Path(tmpdir) / "test.db")},
            "storage": {"path": str(Path(tmpdir) / "docs")},
            "server": {"host": "0.0.0.0", "port": 8100},
            "version": "0.1.0-test",
            "node": {"id": "test-node", "name": "Test", "role": "hub", "community": "test"},
            "sync": {
                "interval_seconds": 30,
                "batch_size": 50,
                "max_document_size_bytes": 10485760,
                "retry_max": 5,
                "retry_backoff_seconds": 5,
            },
            "transport": {
                "tcp": {"enabled": False, "port": 8101, "mdns_name": "_test._tcp.local."},
                "redis": {"enabled": False, "url": "redis://localhost:6379", "channel_prefix": "test:sync:"},
                "serial": {"enabled": False, "device": "/dev/null", "baud_rate": 9600, "chunk_size": 256},
            },
            "discovery": {"mdns_enabled": False, "static_peers": []},
        }
        with patch("sync.app.config.load_config", return_value=test_config):
            # Re-import to pick up patched config
            import importlib
            import sync.app.main as main_mod
            importlib.reload(main_mod)
            with TestClient(main_mod.app) as c:
                yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_and_get_document(client):
    resp = client.post("/api/documents", json={"doc_type": "test", "data": {"key": "val"}})
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["doc_type"] == "test"
    assert doc["data"]["key"] == "val"

    resp2 = client.get(f"/api/documents/{doc['doc_id']}")
    assert resp2.status_code == 200
    assert resp2.json()["doc_id"] == doc["doc_id"]


def test_update_document(client):
    resp = client.post("/api/documents", json={"doc_type": "test", "data": {"a": 1}})
    doc_id = resp.json()["doc_id"]

    resp2 = client.patch(f"/api/documents/{doc_id}", json={"changes": {"b": 2}})
    assert resp2.status_code == 200
    assert resp2.json()["data"]["a"] == 1
    assert resp2.json()["data"]["b"] == 2


def test_delete_document(client):
    resp = client.post("/api/documents", json={"doc_type": "test", "data": {}})
    doc_id = resp.json()["doc_id"]

    resp2 = client.delete(f"/api/documents/{doc_id}")
    assert resp2.status_code == 200

    resp3 = client.get(f"/api/documents/{doc_id}")
    assert resp3.status_code == 404


def test_list_documents(client):
    client.post("/api/documents", json={"doc_type": "alpha", "data": {}})
    client.post("/api/documents", json={"doc_type": "beta", "data": {}})

    resp = client.get("/api/documents")
    assert len(resp.json()) >= 2

    resp2 = client.get("/api/documents?doc_type=alpha")
    assert len(resp2.json()) >= 1


def test_sync_push(client):
    from sync.engine.document import SyncDocument

    remote_doc = SyncDocument(doc_type="test", node_id="remote-node", data={"x": 1})
    remote_doc.vector_clock["remote-node"] = 1
    remote_doc.history.append({
        "node_id": "remote-node",
        "seq": 1,
        "timestamp": remote_doc.created_at,
        "changes": {"x": 1},
    })

    resp = client.post("/api/sync/push", json={
        "sender_id": "remote-node",
        "documents": [remote_doc.to_dict()],
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results[0]["merged"] is True


def test_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "node_id" in data
    assert "document_count" in data


def test_peers_crud(client):
    resp = client.post("/api/peers", json={"host": "192.168.1.10", "port": 8101})
    assert resp.status_code == 200
    peer_id = resp.json()["peer_id"]

    resp2 = client.get("/api/peers")
    assert len(resp2.json()) >= 1

    resp3 = client.delete(f"/api/peers/{peer_id}")
    assert resp3.status_code == 200
