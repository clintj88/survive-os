"""Tests for the Program Enrollment API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


HEADERS = {"X-User": "dr.test", "X-Role": "medical"}


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test_programs.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with seed data loaded."""
    from seed.programs import seed
    seed()
    return client


def _create_program(name: str = "Test Program", desc: str = "A test program") -> int:
    return execute(
        "INSERT INTO programs (name, description) VALUES (?, ?)",
        (name, desc),
    )


def _create_workflow(program_id: int, name: str = "Test Workflow") -> int:
    return execute(
        "INSERT INTO program_workflows (program_id, name, description) VALUES (?, ?, ?)",
        (program_id, name, "Test workflow"),
    )


def _create_state(workflow_id: int, name: str, initial: bool = False, terminal: bool = False, sort_order: int = 0) -> int:
    return execute(
        "INSERT INTO workflow_states (workflow_id, name, initial, terminal, sort_order) VALUES (?, ?, ?, ?, ?)",
        (workflow_id, name, 1 if initial else 0, 1 if terminal else 0, sort_order),
    )


def _create_transition(from_id: int, to_id: int) -> int:
    return execute(
        "INSERT INTO state_transitions (from_state_id, to_state_id) VALUES (?, ?)",
        (from_id, to_id),
    )


def _setup_program_with_workflow() -> dict:
    """Create a program with workflow, states, and transitions for testing."""
    prog_id = _create_program()
    wf_id = _create_workflow(prog_id)
    s1 = _create_state(wf_id, "screening", initial=True, sort_order=1)
    s2 = _create_state(wf_id, "active", sort_order=2)
    s3 = _create_state(wf_id, "completed", terminal=True, sort_order=3)
    _create_transition(s1, s2)
    _create_transition(s2, s3)
    return {"program_id": prog_id, "workflow_id": wf_id, "states": [s1, s2, s3]}


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Auth ---

def test_auth_required(client: TestClient) -> None:
    resp = client.get("/api/programs", headers={"X-User": "", "X-Role": "medical"})
    assert resp.status_code == 401


def test_auth_wrong_role(client: TestClient) -> None:
    resp = client.get("/api/programs", headers={"X-User": "someone", "X-Role": "viewer"})
    assert resp.status_code == 403


# --- Programs CRUD ---

def test_create_program(client: TestClient) -> None:
    resp = client.post("/api/programs", json={
        "name": "TB Treatment",
        "description": "Tuberculosis treatment program",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TB Treatment"
    assert data["active"] == 1


def test_list_programs(client: TestClient) -> None:
    _create_program("Program A")
    _create_program("Program B")
    resp = client.get("/api/programs", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_program(client: TestClient) -> None:
    pid = _create_program("My Program")
    resp = client.get(f"/api/programs/{pid}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "My Program"


def test_get_program_not_found(client: TestClient) -> None:
    resp = client.get("/api/programs/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_program(client: TestClient) -> None:
    pid = _create_program()
    resp = client.put(f"/api/programs/{pid}", json={
        "name": "Updated Name",
        "active": False,
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["active"] == 0


def test_update_program_no_fields(client: TestClient) -> None:
    pid = _create_program()
    resp = client.put(f"/api/programs/{pid}", json={}, headers=HEADERS)
    assert resp.status_code == 400


def test_delete_program(client: TestClient) -> None:
    pid = _create_program()
    resp = client.delete(f"/api/programs/{pid}", headers=HEADERS)
    assert resp.status_code == 204
    resp = client.get(f"/api/programs/{pid}", headers=HEADERS)
    assert resp.status_code == 404


# --- Workflows CRUD ---

def test_create_workflow(client: TestClient) -> None:
    pid = _create_program()
    resp = client.post("/api/workflows", json={
        "program_id": pid,
        "name": "Treatment Workflow",
        "description": "Standard treatment",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Treatment Workflow"
    assert data["program_id"] == pid


def test_create_workflow_program_not_found(client: TestClient) -> None:
    resp = client.post("/api/workflows", json={
        "program_id": 999,
        "name": "Orphan",
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_list_workflows(client: TestClient) -> None:
    pid = _create_program()
    _create_workflow(pid, "WF1")
    _create_workflow(pid, "WF2")
    resp = client.get(f"/api/workflows?program_id={pid}", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_workflow_with_states(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    _create_state(wf, "initial", initial=True, sort_order=1)
    _create_state(wf, "active", sort_order=2)
    resp = client.get(f"/api/workflows/{wf}", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["states"]) == 2
    assert data["states"][0]["name"] == "initial"


def test_delete_workflow(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    resp = client.delete(f"/api/workflows/{wf}", headers=HEADERS)
    assert resp.status_code == 204


# --- States ---

def test_create_state(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    resp = client.post(f"/api/workflows/{wf}/states", json={
        "name": "screening",
        "initial": True,
        "sort_order": 1,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "screening"
    assert data["initial"] == 1


def test_list_states(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    _create_state(wf, "s1", sort_order=1)
    _create_state(wf, "s2", sort_order=2)
    resp = client.get(f"/api/workflows/{wf}/states", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_state(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    sid = _create_state(wf, "deleteme")
    resp = client.delete(f"/api/workflows/states/{sid}", headers=HEADERS)
    assert resp.status_code == 204


# --- Transitions ---

def test_create_transition(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    s1 = _create_state(wf, "from_state")
    s2 = _create_state(wf, "to_state")
    resp = client.post("/api/workflows/transitions", json={
        "from_state_id": s1,
        "to_state_id": s2,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["to_state_name"] == "to_state"


def test_create_transition_cross_workflow(client: TestClient) -> None:
    pid = _create_program()
    wf1 = _create_workflow(pid, "WF1")
    wf2 = _create_workflow(pid, "WF2")
    s1 = _create_state(wf1, "s1")
    s2 = _create_state(wf2, "s2")
    resp = client.post("/api/workflows/transitions", json={
        "from_state_id": s1,
        "to_state_id": s2,
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_delete_transition(client: TestClient) -> None:
    pid = _create_program()
    wf = _create_workflow(pid)
    s1 = _create_state(wf, "s1")
    s2 = _create_state(wf, "s2")
    tid = _create_transition(s1, s2)
    resp = client.delete(f"/api/workflows/transitions/{tid}", headers=HEADERS)
    assert resp.status_code == 204


# --- Enrollments ---

def test_create_enrollment(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_id"] == "P-TEST001"
    assert data["outcome"] == "active"
    assert data["current_state"] == "screening"


def test_create_enrollment_inactive_program(client: TestClient) -> None:
    pid = execute("INSERT INTO programs (name, active) VALUES (?, ?)", ("Inactive", 0))
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": pid,
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_create_enrollment_no_workflow(client: TestClient) -> None:
    pid = _create_program("No Workflow")
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": pid,
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_get_enrollment(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]
    resp = client.get(f"/api/enrollments/{eid}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["current_state"] == "screening"


def test_list_enrollments(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    resp = client.get("/api/enrollments", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_enrollments_filter_by_patient(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST002",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    resp = client.get("/api/enrollments?patient_id=P-TEST001", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- State Transitions ---

def test_transition_state(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    resp = client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][1],
        "changed_by": "dr.test",
        "reason": "Screening complete",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["current_state"] == "active"


def test_transition_invalid(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    # Try to skip from screening directly to completed (not allowed)
    resp = client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][2],
        "changed_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_transition_to_terminal_completes_enrollment(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    # screening -> active
    client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][1],
        "changed_by": "dr.test",
    }, headers=HEADERS)

    # active -> completed (terminal)
    resp = client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][2],
        "changed_by": "dr.test",
        "reason": "Treatment complete",
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome"] == "completed"
    assert data["completion_date"] is not None


def test_transition_already_completed(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    # Complete via API
    client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][1],
        "changed_by": "dr.test",
    }, headers=HEADERS)
    client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][2],
        "changed_by": "dr.test",
    }, headers=HEADERS)

    # Try another transition on completed enrollment
    resp = client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][1],
        "changed_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 400


# --- Enrollment History ---

def test_enrollment_history(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    client.post(f"/api/enrollments/{eid}/transition", json={
        "to_state_id": setup["states"][1],
        "changed_by": "dr.test",
        "reason": "Moved to active",
    }, headers=HEADERS)

    resp = client.get(f"/api/enrollments/{eid}/history", headers=HEADERS)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["state_name"] == "screening"
    assert history[1]["state_name"] == "active"


def test_enrollment_history_not_found(client: TestClient) -> None:
    resp = client.get("/api/enrollments/999/history", headers=HEADERS)
    assert resp.status_code == 404


# --- Complete Enrollment ---

def test_complete_enrollment(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    resp = client.post(f"/api/enrollments/{eid}/complete", json={
        "outcome": "defaulted",
        "changed_by": "dr.test",
        "reason": "Lost to follow-up",
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["outcome"] == "defaulted"
    assert data["completion_date"] is not None


def test_complete_enrollment_invalid_outcome(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    resp = client.post(f"/api/enrollments/{eid}/complete", json={
        "outcome": "invalid_outcome",
        "changed_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_complete_already_completed(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    resp = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    eid = resp.json()["id"]

    client.post(f"/api/enrollments/{eid}/complete", json={
        "outcome": "completed",
        "changed_by": "dr.test",
    }, headers=HEADERS)

    resp = client.post(f"/api/enrollments/{eid}/complete", json={
        "outcome": "defaulted",
        "changed_by": "dr.test",
    }, headers=HEADERS)
    assert resp.status_code == 400


# --- Program Enrollments List ---

def test_program_enrollments(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST002",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)

    resp = client.get(f"/api/programs/{setup['program_id']}/enrollments", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_program_enrollments_filter_active(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    # Create two enrollments
    resp1 = client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST002",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)

    # Complete one
    eid = resp1.json()["id"]
    client.post(f"/api/enrollments/{eid}/complete", json={
        "outcome": "completed",
        "changed_by": "dr.test",
    }, headers=HEADERS)

    resp = client.get(f"/api/programs/{setup['program_id']}/enrollments?status=active", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_program_enrollments_not_found(client: TestClient) -> None:
    resp = client.get("/api/programs/999/enrollments", headers=HEADERS)
    assert resp.status_code == 404


# --- Dashboard ---

def test_dashboard(client: TestClient) -> None:
    setup = _setup_program_with_workflow()
    client.post("/api/enrollments", json={
        "patient_id": "P-TEST001",
        "program_id": setup["program_id"],
        "enrolled_by": "dr.test",
    }, headers=HEADERS)

    resp = client.get("/api/programs/dashboard", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["program_name"] == "Test Program"
    assert data[0]["active_enrollments"] == 1
    assert data[0]["states"]["screening"] == 1


def test_dashboard_empty(client: TestClient) -> None:
    resp = client.get("/api/programs/dashboard", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


# --- Seed Data ---

def test_seed_data(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/programs", headers=HEADERS)
    assert resp.status_code == 200
    programs = resp.json()
    names = {p["name"] for p in programs}
    assert "TB Treatment" in names
    assert "HIV Care" in names
    assert "Diabetes Management" in names
    assert "Prenatal Care" in names


def test_seed_tb_workflow(seeded_client: TestClient) -> None:
    programs = seeded_client.get("/api/programs", headers=HEADERS).json()
    tb = next(p for p in programs if p["name"] == "TB Treatment")
    workflows = seeded_client.get(f"/api/workflows?program_id={tb['id']}", headers=HEADERS).json()
    assert len(workflows) >= 1

    wf = seeded_client.get(f"/api/workflows/{workflows[0]['id']}", headers=HEADERS).json()
    state_names = [s["name"] for s in wf["states"]]
    assert "screening" in state_names
    assert "intensive_phase" in state_names
    assert "completed" in state_names

    # Verify initial and terminal states
    initial_states = [s for s in wf["states"] if s["initial"]]
    terminal_states = [s for s in wf["states"] if s["terminal"]]
    assert len(initial_states) >= 1
    assert len(terminal_states) >= 1


def test_seed_idempotent(seeded_client: TestClient) -> None:
    """Running seed twice should not duplicate data."""
    from seed.programs import seed
    seed()
    resp = seeded_client.get("/api/programs", headers=HEADERS)
    assert len(resp.json()) == 4
