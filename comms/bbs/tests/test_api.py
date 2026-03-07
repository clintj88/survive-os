"""Tests for the BBS API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, seed_topics, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()
    seed_topics(["General", "Trade", "Security"])


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with a thread and post already created."""
    client.post("/api/threads", json={
        "topic_id": 1,
        "title": "Test Thread",
        "author": "testuser",
        "content": "This is the first post.",
    })
    return client


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_list_topics(client: TestClient) -> None:
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    topics = resp.json()
    assert len(topics) == 3
    slugs = {t["slug"] for t in topics}
    assert "general" in slugs
    assert "trade" in slugs


def test_get_topic(client: TestClient) -> None:
    resp = client.get("/api/topics/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "General"


def test_get_topic_not_found(client: TestClient) -> None:
    resp = client.get("/api/topics/999")
    assert resp.status_code == 404


def test_create_thread(client: TestClient) -> None:
    resp = client.post("/api/threads", json={
        "topic_id": 1,
        "title": "New Thread",
        "author": "alice",
        "content": "Hello world!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Thread"
    assert data["author"] == "alice"


def test_create_thread_bad_topic(client: TestClient) -> None:
    resp = client.post("/api/threads", json={
        "topic_id": 999,
        "title": "Bad",
        "author": "alice",
        "content": "test",
    })
    assert resp.status_code == 400


def test_list_threads(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/topics/1/threads")
    assert resp.status_code == 200
    threads = resp.json()
    assert len(threads) == 1
    assert threads[0]["title"] == "Test Thread"
    assert threads[0]["post_count"] == 1


def test_list_threads_topic_not_found(client: TestClient) -> None:
    resp = client.get("/api/topics/999/threads")
    assert resp.status_code == 404


def test_get_thread(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/threads/1")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Thread"


def test_get_thread_not_found(client: TestClient) -> None:
    resp = client.get("/api/threads/999")
    assert resp.status_code == 404


def test_list_posts(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/threads/1/posts")
    assert resp.status_code == 200
    posts = resp.json()
    assert len(posts) == 1
    assert posts[0]["content"] == "This is the first post."


def test_create_post(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/threads/1/posts", json={
        "author": "bob",
        "content": "A reply!",
    })
    assert resp.status_code == 201
    assert resp.json()["author"] == "bob"


def test_create_post_thread_not_found(client: TestClient) -> None:
    resp = client.post("/api/threads/999/posts", json={
        "author": "bob",
        "content": "test",
    })
    assert resp.status_code == 404


def test_create_reply_to_post(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/threads/1/posts", json={
        "author": "carol",
        "content": "Replying to first post",
        "parent_id": 1,
    })
    assert resp.status_code == 201
    assert resp.json()["parent_id"] == 1


def test_create_reply_bad_parent(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/threads/1/posts", json={
        "author": "carol",
        "content": "test",
        "parent_id": 999,
    })
    assert resp.status_code == 400


def test_update_post(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/posts/1", json={
        "content": "Updated content",
    })
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated content"


def test_update_post_not_found(client: TestClient) -> None:
    resp = client.put("/api/posts/999", json={"content": "x"})
    assert resp.status_code == 404


def test_delete_post(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/posts/1")
    assert resp.status_code == 204


def test_delete_post_not_found(client: TestClient) -> None:
    resp = client.delete("/api/posts/999")
    assert resp.status_code == 404


def test_search(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/search?q=first")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1


def test_search_empty(client: TestClient) -> None:
    resp = client.get("/api/search?q=zzzznonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_locked_thread(seeded_client: TestClient) -> None:
    execute("UPDATE threads SET locked = 1 WHERE id = 1", ())
    resp = seeded_client.post("/api/threads/1/posts", json={
        "author": "bob",
        "content": "Should fail",
    })
    assert resp.status_code == 403


def test_sync_status(client: TestClient) -> None:
    resp = client.get("/api/sync/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine"] == "automerge"
