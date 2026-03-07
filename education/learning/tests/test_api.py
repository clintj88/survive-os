"""Tests for the Education & Learning API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _seed_skills(trade: str = "farming") -> None:
    skills = ["Soil preparation", "Seed selection", "Planting"]
    for i, skill in enumerate(skills):
        execute(
            "INSERT INTO skill_checklists (trade, skill_name, sort_order) VALUES (?, ?, ?)",
            (trade, skill, i),
        )


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_create_and_list_apprentice(client: TestClient) -> None:
    resp = client.post("/api/apprentices", json={
        "person_name": "Alice",
        "trade": "farming",
        "mentor_name": "Bob",
    })
    assert resp.status_code == 201
    assert resp.json()["person_name"] == "Alice"

    resp = client.get("/api/apprentices")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/apprentices?trade=farming")
    assert len(resp.json()) == 1

    resp = client.get("/api/apprentices?trade=medical")
    assert len(resp.json()) == 0


def test_apprentice_skills_auto_created(client: TestClient) -> None:
    _seed_skills()
    resp = client.post("/api/apprentices", json={
        "person_name": "Charlie",
        "trade": "farming",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["skills"]) == 3
    assert all(s["status"] == "not_started" for s in data["skills"])


def test_update_skill_status(client: TestClient) -> None:
    _seed_skills()
    resp = client.post("/api/apprentices", json={
        "person_name": "Dana",
        "trade": "farming",
    })
    apprentice = resp.json()
    skill_id = apprentice["skills"][0]["skill_id"]

    resp = client.put(f"/api/apprentices/{apprentice['id']}/skills/{skill_id}", json={
        "status": "in_progress",
    })
    assert resp.status_code == 200
    updated_skill = next(s for s in resp.json()["skills"] if s["skill_id"] == skill_id)
    assert updated_skill["status"] == "in_progress"


def test_apprentice_progress(client: TestClient) -> None:
    _seed_skills()
    resp = client.post("/api/apprentices", json={
        "person_name": "Eve",
        "trade": "farming",
    })
    apprentice = resp.json()
    assert apprentice["progress_pct"] == 0.0

    for skill in apprentice["skills"]:
        client.put(
            f"/api/apprentices/{apprentice['id']}/skills/{skill['skill_id']}",
            json={"status": "demonstrated"},
        )

    resp = client.get(f"/api/apprentices/{apprentice['id']}")
    assert resp.json()["progress_pct"] == 100.0


def test_create_and_list_lessons(client: TestClient) -> None:
    resp = client.post("/api/lessons", json={
        "title": "Basic Math",
        "subject": "math",
        "age_group": "children",
        "duration": "30 minutes",
        "objectives": ["Count to 10", "Add single digits"],
        "procedure": ["Warm up", "Practice"],
        "assessment": "Complete worksheet",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "Basic Math"

    resp = client.get("/api/lessons")
    assert len(resp.json()) == 1

    resp = client.get("/api/lessons?subject=math")
    assert len(resp.json()) == 1

    resp = client.get("/api/lessons?age_group=adult")
    assert len(resp.json()) == 0


def test_search_lessons(client: TestClient) -> None:
    client.post("/api/lessons", json={
        "title": "First Aid",
        "subject": "health",
        "objectives": [],
        "procedure": [],
    })
    resp = client.get("/api/lessons/search?q=first")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_create_curriculum(client: TestClient) -> None:
    resp = client.post("/api/curricula", json={
        "subject": "mathematics",
        "grade_level": "elementary",
        "topic_sequence": ["counting", "addition", "subtraction"],
        "recommended_resources": ["workbook-1"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "mathematics"
    assert len(data["topic_sequence"]) == 3

    resp = client.get("/api/curricula")
    assert len(resp.json()) == 1


def test_math_generation(client: TestClient) -> None:
    resp = client.get("/api/children/math?type=addition&difficulty=1&count=3")
    assert resp.status_code == 200
    problems = resp.json()
    assert len(problems) == 3
    assert all("question" in p and "answer" in p for p in problems)


def test_math_submission(client: TestClient) -> None:
    resp = client.post("/api/children/math/submit", json={
        "child_name": "Timmy",
        "exercise_type": "addition",
        "difficulty": 1,
        "answers": [
            {"user_answer": 5, "correct_answer": 5},
            {"user_answer": 3, "correct_answer": 4},
        ],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 1
    assert data["total"] == 2


def test_reading_exercises(client: TestClient) -> None:
    import json
    execute(
        "INSERT INTO reading_passages (title, difficulty, passage, questions) VALUES (?, ?, ?, ?)",
        ("Test", 1, "A test passage.", json.dumps([{"question": "What?", "answer": "Test"}])),
    )
    resp = client.get("/api/children/reading?difficulty=1")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_children_progress(client: TestClient) -> None:
    execute(
        "INSERT INTO children_progress (child_name, exercise_type, difficulty, score, total) VALUES (?, ?, ?, ?, ?)",
        ("Timmy", "math", 1, 4, 5),
    )
    resp = client.get("/api/children/progress?child_name=Timmy")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_external_resources(client: TestClient) -> None:
    resp = client.get("/api/external/resources")
    assert resp.status_code == 200
    resources = resp.json()
    assert len(resources) == 3
    assert any(r["type"] == "kiwix" for r in resources)


def test_skill_checklists(client: TestClient) -> None:
    _seed_skills("medical")
    resp = client.get("/api/skill-checklists")
    assert resp.status_code == 200
    data = resp.json()
    assert "medical" in data
    assert len(data["medical"]) == 3
