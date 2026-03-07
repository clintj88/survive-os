"""Tests for the Lab Results Tracking API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


HEADERS = {"X-User": "dr.test", "X-Role": "medical"}


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test_lab.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with seed data loaded."""
    from seed.common_tests import seed
    seed()
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Auth ---

def test_auth_required(client: TestClient) -> None:
    resp = client.get("/api/catalog", headers={"X-User": "", "X-Role": "medical"})
    assert resp.status_code == 401


def test_auth_wrong_role(client: TestClient) -> None:
    resp = client.get("/api/catalog", headers={"X-User": "someone", "X-Role": "viewer"})
    assert resp.status_code == 403


# --- Test Catalog ---

def test_create_test(client: TestClient) -> None:
    resp = client.post("/api/catalog", json={
        "name": "CRP",
        "specimen_type": "blood",
        "ref_range_min": 0.0,
        "ref_range_max": 10.0,
        "units": "mg/L",
        "description": "C-Reactive Protein",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "CRP"
    assert data["units"] == "mg/L"
    assert data["active"] == 1


def test_list_tests(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/catalog", headers=HEADERS)
    assert resp.status_code == 200
    tests = resp.json()
    assert len(tests) >= 18
    names = {t["name"] for t in tests}
    assert "WBC" in names
    assert "Glucose" in names


def test_list_tests_filter_specimen(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/catalog?specimen_type=urine", headers=HEADERS)
    assert resp.status_code == 200
    tests = resp.json()
    assert all(t["specimen_type"] == "urine" for t in tests)
    assert any(t["name"] == "Urinalysis" for t in tests)


def test_get_test(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/catalog/1", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "WBC"


def test_get_test_not_found(client: TestClient) -> None:
    resp = client.get("/api/catalog/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_test(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/catalog/1", json={
        "units": "x10^9/L (updated)",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["units"] == "x10^9/L (updated)"


def test_delete_test(client: TestClient) -> None:
    execute(
        """INSERT INTO test_catalog (name, specimen_type, units) VALUES (?, ?, ?)""",
        ("Temp Test", "blood", "mg/dL"),
    )
    resp = client.delete("/api/catalog/1", headers=HEADERS)
    assert resp.status_code == 204
    resp = client.get("/api/catalog/1", headers=HEADERS)
    assert resp.status_code == 404


# --- Panels ---

def test_create_panel(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/panels", json={
        "name": "Custom Panel",
        "description": "Test panel",
        "test_ids": [1, 2, 3],
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Panel"
    assert len(data["tests"]) == 3


def test_list_panels(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/panels", headers=HEADERS)
    assert resp.status_code == 200
    panels = resp.json()
    assert len(panels) >= 2
    names = {p["name"] for p in panels}
    assert "CBC" in names
    assert "BMP" in names


def test_get_panel(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/panels/1", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "CBC"
    assert len(data["tests"]) == 5


def test_get_panel_not_found(client: TestClient) -> None:
    resp = client.get("/api/panels/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_panel(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/panels/1", json={
        "description": "Updated CBC panel",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated CBC panel"


def test_update_panel_tests(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/panels/1", json={
        "test_ids": [1, 2],
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()["tests"]) == 2


def test_delete_panel(seeded_client: TestClient) -> None:
    # Create a throwaway panel
    execute("INSERT INTO lab_panels (name, description) VALUES (?, ?)", ("Temp", "temp"))
    resp = seeded_client.delete("/api/panels/3", headers=HEADERS)
    assert resp.status_code == 204


# --- Orders ---

def test_create_order_single_test(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/orders", json={
        "patient_id": "P-001",
        "test_id": 1,
        "priority": "routine",
        "clinical_indication": "Annual checkup",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_id"] == "P-001"
    assert data["test_id"] == 1
    assert data["status"] == "ordered"


def test_create_order_panel(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/orders", json={
        "patient_id": "P-001",
        "panel_id": 1,
        "priority": "urgent",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    # Panel order creates individual orders for each test
    assert isinstance(data, list)
    assert len(data) == 5  # CBC has 5 tests
    assert all(o["panel_id"] == 1 for o in data)


def test_create_order_missing_ids(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/orders", json={
        "patient_id": "P-001",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_create_order_test_not_found(seeded_client: TestClient) -> None:
    resp = seeded_client.post("/api/orders", json={
        "patient_id": "P-001",
        "test_id": 999,
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_list_orders(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.get("/api/orders", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_orders_by_patient(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-002", 2, "dr.test", "routine"),
    )
    resp = seeded_client.get("/api/orders?patient_id=P-001", headers=HEADERS)
    assert resp.status_code == 200
    orders = resp.json()
    assert all(o["patient_id"] == "P-001" for o in orders)


def test_get_order(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.get("/api/orders/1", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["patient_id"] == "P-001"


def test_order_status_workflow(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "stat"),
    )
    # ordered -> collected
    resp = seeded_client.put("/api/orders/1/status", json={"status": "collected"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "collected"
    assert resp.json()["collected_at"] is not None

    # collected -> processing
    resp = seeded_client.put("/api/orders/1/status", json={"status": "processing"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"

    # processing -> completed
    resp = seeded_client.put("/api/orders/1/status", json={"status": "completed"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_order_invalid_transition(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    # ordered -> completed is not valid (must go through collected, processing)
    resp = seeded_client.put("/api/orders/1/status", json={"status": "completed"}, headers=HEADERS)
    assert resp.status_code == 400


def test_order_cancel(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.put("/api/orders/1/status", json={"status": "cancelled"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# --- Results ---

def test_create_result_normal(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.post("/api/results", json={
        "order_id": 1,
        "test_id": 1,
        "value": "7.5",
        "numeric_value": 7.5,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["interpretation"] == "normal"
    assert data["units"] == "x10^9/L"

    # Order should be auto-completed
    order = query("SELECT status FROM lab_orders WHERE id = 1")
    assert order[0]["status"] == "completed"


def test_create_result_abnormal_high(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.post("/api/results", json={
        "order_id": 1,
        "test_id": 1,
        "value": "15.0",
        "numeric_value": 15.0,
    }, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["interpretation"] == "abnormal"


def test_create_result_critical_low(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.post("/api/results", json={
        "order_id": 1,
        "test_id": 1,
        "value": "1.5",
        "numeric_value": 1.5,
    }, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["interpretation"] == "critical_low"


def test_create_result_critical_high(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    resp = seeded_client.post("/api/results", json={
        "order_id": 1,
        "test_id": 1,
        "value": "35.0",
        "numeric_value": 35.0,
    }, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["interpretation"] == "critical_high"


def test_alerts(seeded_client: TestClient) -> None:
    # Create order + abnormal result
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 1, "15.0", 15.0, "x10^9/L", "abnormal"),
    )
    resp = seeded_client.get("/api/results/alerts", headers=HEADERS)
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) >= 1
    assert alerts[0]["interpretation"] == "abnormal"


def test_alerts_by_patient(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 1, "15.0", 15.0, "x10^9/L", "abnormal"),
    )
    resp = seeded_client.get("/api/results/alerts?patient_id=P-001", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = seeded_client.get("/api/results/alerts?patient_id=P-999", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_trends(seeded_client: TestClient) -> None:
    for i, val in enumerate([7.0, 8.5, 12.0]):
        oid = execute(
            """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
               VALUES (?, ?, ?, ?)""",
            ("P-001", 1, "dr.test", "routine"),
        )
        execute(
            """INSERT INTO lab_results (order_id, test_id, numeric_value, units, interpretation, result_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (oid, 1, val, "x10^9/L", "normal", f"2026-03-0{i+1}"),
        )
    resp = seeded_client.get("/api/results/trends/P-001/1", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["numeric_value"] == 7.0
    assert data[2]["numeric_value"] == 12.0


def test_patient_results(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation, result_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (1, 1, "7.5", 7.5, "x10^9/L", "normal", "2026-03-01"),
    )
    resp = seeded_client.get("/api/results/patient/P-001", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["test_name"] == "WBC"


def test_patient_results_filter_test(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 2, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 1, "7.5", 7.5, "x10^9/L", "normal"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (2, 2, "5.0", 5.0, "x10^12/L", "normal"),
    )
    resp = seeded_client.get("/api/results/patient/P-001?test_id=1", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert all(r["test_id"] == 1 for r in results)


def test_patient_results_filter_date(seeded_client: TestClient) -> None:
    execute(
        """INSERT INTO lab_orders (patient_id, test_id, ordered_by, priority)
           VALUES (?, ?, ?, ?)""",
        ("P-001", 1, "dr.test", "routine"),
    )
    execute(
        """INSERT INTO lab_results (order_id, test_id, value, numeric_value, units, interpretation, result_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (1, 1, "7.5", 7.5, "x10^9/L", "normal", "2026-03-01"),
    )
    resp = seeded_client.get(
        "/api/results/patient/P-001?date_from=2026-03-01&date_to=2026-03-31",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = seeded_client.get(
        "/api/results/patient/P-001?date_from=2026-04-01",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# --- Seed data ---

def test_seed_idempotent(seeded_client: TestClient) -> None:
    """Running seed twice should not duplicate data."""
    from seed.common_tests import seed
    count_before = query("SELECT COUNT(*) AS cnt FROM test_catalog")[0]["cnt"]
    seed()  # run again
    count_after = query("SELECT COUNT(*) AS cnt FROM test_catalog")[0]["cnt"]
    assert count_before == count_after
