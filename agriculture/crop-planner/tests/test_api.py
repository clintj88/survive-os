"""Tests for the Crop Rotation Planner API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, execute_many, init_db, query, set_db_path
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
def seeded_db() -> None:
    """Seed the database with test data."""
    from seed.rotations import seed_defaults
    from seed.companions import seed_companions
    seed_defaults()
    seed_companions()


@pytest.fixture
def seeded_client(client: TestClient, seeded_db: None) -> TestClient:
    return client


@pytest.fixture
def field_with_plots(seeded_db: None) -> int:
    """Create a field with plots and return the field_id."""
    field_id = execute(
        "INSERT INTO fields (name, rows, cols) VALUES (?, ?, ?)",
        ("Test Field", 3, 3),
    )
    execute_many(
        "INSERT INTO plots (field_id, row_idx, col_idx, label) VALUES (?, ?, ?, ?)",
        [(field_id, r, c, f"{chr(65+r)}{c+1}") for r in range(3) for c in range(3)],
    )
    return field_id


# Health check
def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# Crops
def test_list_crops_empty(client: TestClient) -> None:
    resp = client.get("/api/crops")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_crops_seeded(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/crops")
    assert resp.status_code == 200
    crops = resp.json()
    assert len(crops) > 10


def test_list_crops_by_group(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/crops?group=legume")
    assert resp.status_code == 200
    crops = resp.json()
    assert all(c["rotation_group"] == "legume" for c in crops)


def test_create_crop(client: TestClient) -> None:
    resp = client.post("/api/crops", json={
        "name": "Test Crop",
        "family": "Testaceae",
        "rotation_group": "fruit",
        "days_to_maturity": 60,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Test Crop"


def test_get_crop(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/crops/1")
    assert resp.status_code == 200
    assert "name" in resp.json()


def test_get_crop_not_found(client: TestClient) -> None:
    resp = client.get("/api/crops/999")
    assert resp.status_code == 404


# Fields
def test_create_field(client: TestClient) -> None:
    resp = client.post("/api/fields", json={
        "name": "North Garden",
        "rows": 3,
        "cols": 4,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "North Garden"
    assert len(data["plots"]) == 12


def test_list_fields(client: TestClient) -> None:
    client.post("/api/fields", json={"name": "Field A"})
    resp = client.get("/api/fields")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_field(client: TestClient) -> None:
    client.post("/api/fields", json={"name": "Field B"})
    resp = client.get("/api/fields/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Field B"


def test_get_field_not_found(client: TestClient) -> None:
    resp = client.get("/api/fields/999")
    assert resp.status_code == 404


def test_update_field(client: TestClient) -> None:
    client.post("/api/fields", json={"name": "Old Name"})
    resp = client.put("/api/fields/1", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_field(client: TestClient) -> None:
    client.post("/api/fields", json={"name": "Doomed"})
    resp = client.delete("/api/fields/1")
    assert resp.status_code == 204


def test_list_plots(client: TestClient) -> None:
    client.post("/api/fields", json={"name": "Plot Field", "rows": 2, "cols": 2})
    resp = client.get("/api/fields/1/plots")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


# Plot assignment
def test_assign_crop_to_plot(seeded_client: TestClient) -> None:
    seeded_client.post("/api/fields", json={"name": "Assign Field", "rows": 2, "cols": 2})
    plots = seeded_client.get("/api/fields/1/plots").json()
    plot_id = plots[0]["id"]
    crops = seeded_client.get("/api/crops").json()
    crop_id = crops[0]["id"]

    resp = seeded_client.post(f"/api/fields/1/plots/{plot_id}/assign", json={
        "crop_id": crop_id,
        "season": "spring",
        "year": 2026,
    })
    assert resp.status_code == 201
    assert resp.json()["crop_id"] == crop_id


# Rotation templates
def test_list_templates(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/rotations/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 2
    assert templates[0]["steps"]


def test_create_template(client: TestClient) -> None:
    resp = client.post("/api/rotations/templates", json={
        "name": "Custom Rotation",
        "climate_zone": "arid",
        "steps": [
            {"rotation_group": "legume", "year_offset": 0},
            {"rotation_group": "root", "year_offset": 1},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Rotation"
    assert len(data["steps"]) == 2


def test_update_template(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/rotations/templates/1", json={
        "description": "Updated description",
    })
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


def test_delete_template(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/rotations/templates/1")
    assert resp.status_code == 204


# Rotation suggestion
def test_suggest_no_history(seeded_client: TestClient, field_with_plots: int) -> None:
    plots = query("SELECT id FROM plots WHERE field_id = ? LIMIT 1", (field_with_plots,))
    plot_id = plots[0]["id"]
    resp = seeded_client.get(f"/api/rotations/suggest/{plot_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["suggestion"] == "legume"


def test_suggest_with_history(seeded_client: TestClient, field_with_plots: int) -> None:
    plots = query("SELECT id FROM plots WHERE field_id = ? LIMIT 1", (field_with_plots,))
    plot_id = plots[0]["id"]
    legume = query("SELECT id FROM crops WHERE rotation_group = 'legume' LIMIT 1")
    crop_id = legume[0]["id"]
    execute(
        "INSERT INTO plot_assignments (plot_id, crop_id, season, year) VALUES (?, ?, ?, ?)",
        (plot_id, crop_id, "spring", 2025),
    )
    resp = seeded_client.get(f"/api/rotations/suggest/{plot_id}")
    assert resp.status_code == 200
    assert resp.json()["suggestion"] == "leaf"


# Companions
def test_list_companions(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/companions")
    assert resp.status_code == 200
    assert len(resp.json()) > 10


def test_list_companions_by_crop(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/companions?crop=Tomato")
    assert resp.status_code == 200
    companions = resp.json()
    assert all("Tomato" in (c["crop_a"], c["crop_b"]) for c in companions)


def test_check_compatibility(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/companions/check?crop_a=Basil&crop_b=Tomato")
    assert resp.status_code == 200
    assert resp.json()["relationship"] == "beneficial"


def test_check_compatibility_unknown(client: TestClient) -> None:
    resp = client.get("/api/companions/check?crop_a=FakeCrop&crop_b=AnotherFake")
    assert resp.status_code == 200
    assert resp.json()["relationship"] == "unknown"


def test_create_companion(client: TestClient) -> None:
    resp = client.post("/api/companions", json={
        "crop_a": "Apple",
        "crop_b": "Mint",
        "relationship": "beneficial",
        "notes": "Mint deters apple pests",
    })
    assert resp.status_code == 201
    assert resp.json()["relationship"] == "beneficial"


# Calendar
def test_frost_dates(client: TestClient) -> None:
    resp = client.get("/api/calendar/frost-dates?year=2026")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == 2026
    assert "last_spring_frost" in data
    assert "first_fall_frost" in data
    assert data["growing_season_days"] > 0


def test_planting_windows(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/calendar/planting-windows?year=2026")
    assert resp.status_code == 200
    windows = resp.json()
    assert len(windows) > 10
    assert "crop_name" in windows[0]


def test_planting_window_single(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/calendar/planting-windows/1?year=2026")
    assert resp.status_code == 200
    assert "crop_name" in resp.json()


def test_month_events(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/calendar/month/2026/4")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)


# Yields
def test_record_and_list_yields(seeded_client: TestClient, field_with_plots: int) -> None:
    plots = query("SELECT id FROM plots WHERE field_id = ? LIMIT 1", (field_with_plots,))
    plot_id = plots[0]["id"]
    crop = query("SELECT id FROM crops LIMIT 1")
    crop_id = crop[0]["id"]

    resp = seeded_client.post("/api/yields", json={
        "plot_id": plot_id,
        "crop_id": crop_id,
        "year": 2025,
        "season": "spring",
        "amount": 15.5,
        "unit": "kg",
    })
    assert resp.status_code == 201
    assert resp.json()["amount"] == 15.5

    resp = seeded_client.get(f"/api/yields?plot_id={plot_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_predict_yield_no_data(seeded_client: TestClient, field_with_plots: int) -> None:
    plots = query("SELECT id FROM plots WHERE field_id = ? LIMIT 1", (field_with_plots,))
    plot_id = plots[0]["id"]
    crop = query("SELECT id FROM crops LIMIT 1")
    crop_id = crop[0]["id"]

    resp = seeded_client.get(f"/api/yields/predict?plot_id={plot_id}&crop_id={crop_id}")
    assert resp.status_code == 200
    assert resp.json()["predicted_yield"] is None


def test_predict_yield_with_data(seeded_client: TestClient, field_with_plots: int) -> None:
    plots = query("SELECT id FROM plots WHERE field_id = ? LIMIT 1", (field_with_plots,))
    plot_id = plots[0]["id"]
    crop = query("SELECT id FROM crops LIMIT 1")
    crop_id = crop[0]["id"]

    # Insert historical yields
    for yr in range(2020, 2026):
        execute(
            "INSERT INTO yields (plot_id, crop_id, year, season, amount, unit) VALUES (?, ?, ?, ?, ?, ?)",
            (plot_id, crop_id, yr, "spring", 10.0 + yr - 2020, "kg"),
        )

    resp = seeded_client.get(f"/api/yields/predict?plot_id={plot_id}&crop_id={crop_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["predicted_yield"] is not None
    assert data["predicted_yield"] > 0
    assert data["data_points"] == 6
