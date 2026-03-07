"""Tests for the Knowledge Base API."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    """Set up a fresh in-memory database for each test."""
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with a category and article already created."""
    from app.database import execute

    execute(
        "INSERT INTO categories (name, slug, description) VALUES (?, ?, ?)",
        ("First Aid", "first-aid", "Emergency medical care"),
    )
    execute(
        """INSERT INTO articles (title, slug, category_id, content, summary)
           VALUES (?, ?, ?, ?, ?)""",
        ("Test Article", "test-article", 1, "# Test Content\n\nBody text.", "A test article."),
    )
    return client


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_list_categories_empty(client: TestClient) -> None:
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_categories(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) == 1
    assert cats[0]["slug"] == "first-aid"


def test_list_articles(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/articles")
    assert resp.status_code == 200
    articles = resp.json()
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article"


def test_list_articles_by_category(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/articles?category=first-aid")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = seeded_client.get("/api/articles?category=nonexistent")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_article(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/articles/1")
    assert resp.status_code == 200
    article = resp.json()
    assert article["title"] == "Test Article"
    assert "# Test Content" in article["content"]


def test_get_article_not_found(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/articles/999")
    assert resp.status_code == 404


def test_create_article(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/articles", json={
        "title": "New Article",
        "category_id": 1,
        "content": "New content here.",
        "summary": "A new article.",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Article"
    assert data["id"] == 2


def test_create_article_bad_category(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/articles", json={
        "title": "Bad",
        "category_id": 999,
        "content": "Content",
    })
    assert resp.status_code == 400


def test_update_article(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/articles/1", json={
        "title": "Updated Title",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_update_article_not_found(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/articles/999", json={"title": "X"})
    assert resp.status_code == 404


def test_search(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/search?q=test")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["title"] == "Test Article"


def test_search_empty(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/search?q=zzzznonexistent")
    assert resp.status_code == 200
    assert resp.json() == []
