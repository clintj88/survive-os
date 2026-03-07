"""Tests for the Drone Aerial Maps API."""

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


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with sample surveys and related data."""
    client.post("/api/surveys", json={
        "name": "North Field Survey",
        "area_name": "North Field",
        "date": "2026-03-01",
        "drone_model": "DJI Mavic 3",
        "operator": "pilot_a",
        "bounds": '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}',
        "status": "completed",
    })
    client.post("/api/surveys", json={
        "name": "South Ridge Recon",
        "area_name": "South Ridge",
        "date": "2026-03-05",
        "drone_model": "DJI Mini 4",
        "operator": "pilot_b",
        "status": "planned",
    })
    # Add images to first survey
    client.post("/api/images", json={
        "survey_id": 1,
        "filename": "IMG_0001.jpg",
        "filepath": "/var/lib/survive/drone-maps/images/IMG_0001.jpg",
        "latitude": 34.05,
        "longitude": -118.25,
        "altitude": 120.0,
        "captured_at": "2026-03-01T10:00:00",
    })
    client.post("/api/images", json={
        "survey_id": 1,
        "filename": "IMG_0002.jpg",
        "filepath": "/var/lib/survive/drone-maps/images/IMG_0002.jpg",
        "latitude": 34.051,
        "longitude": -118.249,
        "altitude": 120.0,
        "captured_at": "2026-03-01T10:01:00",
    })
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Surveys ---

def test_create_survey(client: TestClient) -> None:
    resp = client.post("/api/surveys", json={
        "name": "Test Survey",
        "area_name": "Test Area",
        "drone_model": "Phantom 4",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Survey"
    assert data["area_name"] == "Test Area"
    assert data["status"] == "planned"


def test_create_survey_invalid_status(client: TestClient) -> None:
    resp = client.post("/api/surveys", json={
        "name": "Bad",
        "status": "invalid_status",
    })
    assert resp.status_code == 400


def test_list_surveys(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/surveys")
    assert resp.status_code == 200
    surveys = resp.json()
    assert len(surveys) == 2


def test_list_surveys_filter_status(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/surveys?status=completed")
    assert resp.status_code == 200
    surveys = resp.json()
    assert len(surveys) == 1
    assert surveys[0]["status"] == "completed"


def test_list_surveys_filter_area(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/surveys?area_name=North")
    assert resp.status_code == 200
    surveys = resp.json()
    assert len(surveys) == 1
    assert "North" in surveys[0]["area_name"]


def test_get_survey(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/surveys/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "North Field Survey"


def test_get_survey_not_found(client: TestClient) -> None:
    resp = client.get("/api/surveys/999")
    assert resp.status_code == 404


def test_update_survey(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/surveys/2", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_update_survey_invalid_status(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/surveys/1", json={"status": "bogus"})
    assert resp.status_code == 400


def test_delete_survey(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/surveys/2")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/surveys/2")
    assert resp.status_code == 404


def test_delete_survey_cascades(seeded_client: TestClient) -> None:
    """Deleting a survey removes its images, jobs, changes, and terrain."""
    seeded_client.post("/api/processing", json={"survey_id": 1})
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/dem.tif"})
    resp = seeded_client.delete("/api/surveys/1")
    assert resp.status_code == 200
    assert query("SELECT * FROM images WHERE survey_id = 1") == []
    assert query("SELECT * FROM processing_jobs WHERE survey_id = 1") == []
    assert query("SELECT * FROM terrain_models WHERE survey_id = 1") == []


# --- Images ---

def test_create_image(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/images", json={
        "survey_id": 1,
        "filename": "IMG_0003.jpg",
        "latitude": 34.052,
        "longitude": -118.248,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "IMG_0003.jpg"
    assert data["survey_id"] == 1


def test_create_image_survey_not_found(client: TestClient) -> None:
    resp = client.post("/api/images", json={
        "survey_id": 999,
        "filename": "nope.jpg",
    })
    assert resp.status_code == 404


def test_list_images(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/images")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_images_by_survey(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/images?survey_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = seeded_client.get("/api/images?survey_id=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_image(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/images/1")
    assert resp.status_code == 200
    assert resp.json()["filename"] == "IMG_0001.jpg"


def test_get_image_not_found(client: TestClient) -> None:
    resp = client.get("/api/images/999")
    assert resp.status_code == 404


def test_delete_image(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/images/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/images/1")
    assert resp.status_code == 404


# --- Processing Jobs ---

def test_create_job(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/processing", json={"survey_id": 1})
    assert resp.status_code == 201
    data = resp.json()
    assert data["survey_id"] == 1
    assert data["status"] == "pending"


def test_create_job_survey_not_found(client: TestClient) -> None:
    resp = client.post("/api/processing", json={"survey_id": 999})
    assert resp.status_code == 404


def test_list_jobs(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.get("/api/processing")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_jobs_filter_status(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.get("/api/processing?status=pending")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_job(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.get("/api/processing/1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


def test_get_job_not_found(client: TestClient) -> None:
    resp = client.get("/api/processing/999")
    assert resp.status_code == 404


def test_update_job_status(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.put("/api/processing/1", json={"status": "processing"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"
    assert resp.json()["started_at"] is not None


def test_update_job_invalid_status(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.put("/api/processing/1", json={"status": "bogus"})
    assert resp.status_code == 400


def test_run_job_mock(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    resp = seeded_client.post("/api/processing/1/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["output_path"] != ""
    assert data["resolution"] == 0.05
    assert data["file_size"] == 104857600
    assert data["started_at"] is not None
    assert data["completed_at"] is not None


def test_run_job_not_pending(seeded_client: TestClient) -> None:
    seeded_client.post("/api/processing", json={"survey_id": 1})
    seeded_client.post("/api/processing/1/run")  # completes the job
    resp = seeded_client.post("/api/processing/1/run")  # try again
    assert resp.status_code == 400


def test_run_job_not_found(client: TestClient) -> None:
    resp = client.post("/api/processing/999/run")
    assert resp.status_code == 404


# --- Change Detections ---

def test_create_change(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/changes", json={
        "survey_a_id": 1,
        "survey_b_id": 2,
        "change_type": "new_construction",
        "geometry": '{"type":"Point","coordinates":[-118.25,34.05]}',
        "description": "New building detected",
        "severity": "high",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["change_type"] == "new_construction"
    assert data["severity"] == "high"


def test_create_change_invalid_type(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/changes", json={
        "survey_a_id": 1,
        "survey_b_id": 2,
        "change_type": "invalid_type",
    })
    assert resp.status_code == 400


def test_create_change_invalid_severity(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/changes", json={
        "survey_a_id": 1,
        "survey_b_id": 2,
        "change_type": "erosion",
        "severity": "extreme",
    })
    assert resp.status_code == 400


def test_create_change_survey_not_found(client: TestClient) -> None:
    resp = client.post("/api/changes", json={
        "survey_a_id": 999,
        "survey_b_id": 998,
        "change_type": "erosion",
    })
    assert resp.status_code == 404


def test_list_changes(seeded_client: TestClient) -> None:
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "erosion",
    })
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "crop_changes",
    })
    resp = seeded_client.get("/api/changes")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_changes_filter(seeded_client: TestClient) -> None:
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "erosion",
    })
    resp = seeded_client.get("/api/changes?survey_a_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_change(seeded_client: TestClient) -> None:
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "water_level",
    })
    resp = seeded_client.get("/api/changes/1")
    assert resp.status_code == 200
    assert resp.json()["change_type"] == "water_level"


def test_get_change_not_found(client: TestClient) -> None:
    resp = client.get("/api/changes/999")
    assert resp.status_code == 404


def test_delete_change(seeded_client: TestClient) -> None:
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "other",
    })
    resp = seeded_client.delete("/api/changes/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/changes/1")
    assert resp.status_code == 404


# --- Compare Surveys ---

def test_compare_surveys(seeded_client: TestClient) -> None:
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "erosion",
        "description": "Hillside erosion", "severity": "medium",
    })
    seeded_client.post("/api/changes", json={
        "survey_a_id": 1, "survey_b_id": 2, "change_type": "new_construction",
        "description": "Shed built", "severity": "low",
    })
    resp = seeded_client.get("/api/surveys/1/compare/2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["survey_a_id"] == 1
    assert data["survey_b_id"] == 2
    assert len(data["changes"]) == 2


def test_compare_surveys_not_found(client: TestClient) -> None:
    resp = client.get("/api/surveys/999/compare/998")
    assert resp.status_code == 404


# --- Terrain Models ---

def test_create_terrain(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/terrain", json={
        "survey_id": 1,
        "filepath": "/var/lib/survive/drone-maps/output/dem_north.tif",
        "resolution": 0.1,
        "bounds": '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}',
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["survey_id"] == 1
    assert data["resolution"] == 0.1


def test_create_terrain_survey_not_found(client: TestClient) -> None:
    resp = client.post("/api/terrain", json={
        "survey_id": 999,
        "filepath": "/nope.tif",
    })
    assert resp.status_code == 404


def test_list_terrain(seeded_client: TestClient) -> None:
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/a.tif"})
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/b.tif"})
    resp = seeded_client.get("/api/terrain")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_terrain_by_survey(seeded_client: TestClient) -> None:
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/a.tif"})
    resp = seeded_client.get("/api/terrain?survey_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = seeded_client.get("/api/terrain?survey_id=2")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_terrain(seeded_client: TestClient) -> None:
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/dem.tif"})
    resp = seeded_client.get("/api/terrain/1")
    assert resp.status_code == 200
    assert resp.json()["filepath"] == "/dem.tif"


def test_get_terrain_not_found(client: TestClient) -> None:
    resp = client.get("/api/terrain/999")
    assert resp.status_code == 404


def test_delete_terrain(seeded_client: TestClient) -> None:
    seeded_client.post("/api/terrain", json={"survey_id": 1, "filepath": "/dem.tif"})
    resp = seeded_client.delete("/api/terrain/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/terrain/1")
    assert resp.status_code == 404
