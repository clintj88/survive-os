"""Tests for the Printable Map Generation API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.jobs import set_output_dir
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()
    set_output_dir(str(tmp_path / "output"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_job(client: TestClient, **overrides) -> dict:
    data = {
        "title": "Test Map",
        "center_lat": 34.0522,
        "center_lng": -118.2437,
        "zoom": 13,
        "paper_size": "A4",
        "orientation": "portrait",
        "dpi": 300,
    }
    data.update(overrides)
    resp = client.post("/api/jobs", json=data)
    return resp


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Print Jobs ---

def test_create_job(client: TestClient) -> None:
    resp = _create_job(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Map"
    assert data["center_lat"] == 34.0522
    assert data["center_lng"] == -118.2437
    assert data["paper_size"] == "A4"
    assert data["status"] == "completed"
    assert data["file_size"] > 0


def test_create_job_landscape(client: TestClient) -> None:
    resp = _create_job(client, orientation="landscape")
    assert resp.status_code == 201
    assert resp.json()["orientation"] == "landscape"


def test_create_job_with_overlays(client: TestClient) -> None:
    resp = _create_job(client, overlay_layers=["roads", "water", "buildings"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["overlay_layers"] == ["roads", "water", "buildings"]


def test_create_job_with_elements(client: TestClient) -> None:
    resp = _create_job(
        client,
        include_legend=False,
        include_scale_bar=True,
        include_north_arrow=False,
        include_grid=True,
        include_date=False,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["include_legend"] is False
    assert data["include_scale_bar"] is True
    assert data["include_north_arrow"] is False
    assert data["include_grid"] is True
    assert data["include_date"] is False


def test_create_job_invalid_paper_size(client: TestClient) -> None:
    resp = _create_job(client, paper_size="A0")
    assert resp.status_code == 400


def test_create_job_invalid_orientation(client: TestClient) -> None:
    resp = _create_job(client, orientation="diagonal")
    assert resp.status_code == 400


def test_create_job_invalid_dpi(client: TestClient) -> None:
    resp = _create_job(client, dpi=72)
    assert resp.status_code == 400


def test_create_job_custom_paper_missing_dimensions(client: TestClient) -> None:
    resp = _create_job(client, paper_size="custom")
    assert resp.status_code == 400


def test_create_job_custom_paper(client: TestClient) -> None:
    resp = _create_job(
        client,
        paper_size="custom",
        paper_width_mm=200,
        paper_height_mm=300,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["paper_size"] == "custom"
    assert data["paper_width_mm"] == 200
    assert data["paper_height_mm"] == 300


def test_create_job_invalid_lat(client: TestClient) -> None:
    resp = client.post("/api/jobs", json={
        "center_lat": 100,
        "center_lng": 0,
    })
    assert resp.status_code == 422


def test_create_job_invalid_lng(client: TestClient) -> None:
    resp = client.post("/api/jobs", json={
        "center_lat": 0,
        "center_lng": 200,
    })
    assert resp.status_code == 422


def test_list_jobs(client: TestClient) -> None:
    _create_job(client, title="Job 1")
    _create_job(client, title="Job 2")
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 2


def test_list_jobs_filter_status(client: TestClient) -> None:
    _create_job(client, title="Job 1")
    resp = client.get("/api/jobs?status=completed")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "completed"


def test_list_jobs_filter_no_match(client: TestClient) -> None:
    _create_job(client, title="Job 1")
    resp = client.get("/api/jobs?status=failed")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_get_job(client: TestClient) -> None:
    _create_job(client, title="My Map")
    resp = client.get("/api/jobs/1")
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Map"


def test_get_job_not_found(client: TestClient) -> None:
    resp = client.get("/api/jobs/999")
    assert resp.status_code == 404


def test_delete_job(client: TestClient) -> None:
    _create_job(client, title="To Delete")
    resp = client.delete("/api/jobs/1")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1
    resp = client.get("/api/jobs/1")
    assert resp.status_code == 404


def test_delete_job_not_found(client: TestClient) -> None:
    resp = client.delete("/api/jobs/999")
    assert resp.status_code == 404


def test_download_job(client: TestClient) -> None:
    _create_job(client, title="Download Test")
    resp = client.get("/api/jobs/1/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 0


def test_download_job_not_found(client: TestClient) -> None:
    resp = client.get("/api/jobs/999/download")
    assert resp.status_code == 404


# --- Templates ---

def test_create_template(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "Patrol Route",
        "description": "Standard patrol route map",
        "template_type": "patrol_map",
        "paper_size": "A3",
        "orientation": "landscape",
        "dpi": 300,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Patrol Route"
    assert data["template_type"] == "patrol_map"
    assert data["paper_size"] == "A3"
    assert data["orientation"] == "landscape"


def test_create_template_invalid_type(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "Bad",
        "template_type": "invalid_type",
    })
    assert resp.status_code == 400


def test_create_template_invalid_paper(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "Bad Paper",
        "paper_size": "A0",
    })
    assert resp.status_code == 400


def test_create_template_invalid_orientation(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "Bad Orient",
        "orientation": "sideways",
    })
    assert resp.status_code == 400


def test_create_template_invalid_dpi(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "Bad DPI",
        "dpi": 72,
    })
    assert resp.status_code == 400


def test_create_template_duplicate_name(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "Dupe"})
    resp = client.post("/api/templates", json={"name": "Dupe"})
    assert resp.status_code == 400


def test_list_templates(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "T1", "template_type": "patrol_map"})
    client.post("/api/templates", json={"name": "T2", "template_type": "general"})
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_templates_filter_type(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "T1", "template_type": "patrol_map"})
    client.post("/api/templates", json={"name": "T2", "template_type": "general"})
    resp = client.get("/api/templates?template_type=patrol_map")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) == 1
    assert templates[0]["template_type"] == "patrol_map"


def test_get_template(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "Get Me"})
    resp = client.get("/api/templates/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


def test_get_template_not_found(client: TestClient) -> None:
    resp = client.get("/api/templates/999")
    assert resp.status_code == 404


def test_update_template(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "Original"})
    resp = client.put("/api/templates/1", json={
        "name": "Updated",
        "dpi": 600,
        "include_grid": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["dpi"] == 600
    assert data["include_grid"] is True


def test_update_template_not_found(client: TestClient) -> None:
    resp = client.put("/api/templates/999", json={"name": "Nope"})
    assert resp.status_code == 404


def test_update_template_duplicate_name(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "First"})
    client.post("/api/templates", json={"name": "Second"})
    resp = client.put("/api/templates/2", json={"name": "First"})
    assert resp.status_code == 400


def test_update_template_invalid_type(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "T"})
    resp = client.put("/api/templates/1", json={"template_type": "bad"})
    assert resp.status_code == 400


def test_delete_template(client: TestClient) -> None:
    client.post("/api/templates", json={"name": "Delete Me"})
    resp = client.delete("/api/templates/1")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1
    resp = client.get("/api/templates/1")
    assert resp.status_code == 404


def test_delete_template_not_found(client: TestClient) -> None:
    resp = client.delete("/api/templates/999")
    assert resp.status_code == 404


def test_create_template_with_overlays(client: TestClient) -> None:
    resp = client.post("/api/templates", json={
        "name": "With Layers",
        "overlay_layers": ["roads", "water"],
    })
    assert resp.status_code == 201
    assert resp.json()["overlay_layers"] == ["roads", "water"]


def test_template_element_defaults(client: TestClient) -> None:
    resp = client.post("/api/templates", json={"name": "Defaults"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["include_legend"] is True
    assert data["include_scale_bar"] is True
    assert data["include_north_arrow"] is True
    assert data["include_grid"] is False
    assert data["include_date"] is True


def test_all_paper_sizes(client: TestClient) -> None:
    for size in ["A4", "A3", "letter", "tabloid"]:
        resp = _create_job(client, title=f"{size} map", paper_size=size)
        assert resp.status_code == 201
        assert resp.json()["status"] == "completed"


def test_all_dpi_values(client: TestClient) -> None:
    for dpi in [150, 300, 600]:
        resp = _create_job(client, title=f"{dpi}dpi map", dpi=dpi)
        assert resp.status_code == 201
        assert resp.json()["dpi"] == dpi
