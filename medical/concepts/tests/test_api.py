"""Tests for the Clinical Concept Dictionary API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, query, set_db_path
from app.main import app


HEADERS = {"X-User": "dr.test", "X-Role": "medical"}


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test_concepts.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """Client with seed data loaded."""
    from seed.clinical_concepts import seed_all
    seed_all()
    return client


def _create_concept(client: TestClient, **kwargs) -> dict:
    data = {
        "name": "Test Concept",
        "datatype": "numeric",
        "concept_class": "finding",
        "description": "A test concept",
        "units": "mg",
    }
    data.update(kwargs)
    resp = client.post("/api/concepts", json=data, headers=HEADERS)
    assert resp.status_code == 201
    return resp.json()


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Auth ---

def test_auth_required(client: TestClient) -> None:
    resp = client.get("/api/concepts", headers={"X-User": "", "X-Role": "medical"})
    assert resp.status_code == 401


def test_auth_wrong_role(client: TestClient) -> None:
    resp = client.get("/api/concepts", headers={"X-User": "someone", "X-Role": "viewer"})
    assert resp.status_code == 403


# --- Concepts CRUD ---

def test_create_concept(client: TestClient) -> None:
    concept = _create_concept(client)
    assert concept["name"] == "Test Concept"
    assert concept["datatype"] == "numeric"
    assert concept["concept_class"] == "finding"
    assert concept["units"] == "mg"
    assert concept["retired"] == 0


def test_create_concept_invalid_datatype(client: TestClient) -> None:
    resp = client.post("/api/concepts", json={
        "name": "Bad", "datatype": "invalid", "concept_class": "finding",
    }, headers=HEADERS)
    assert resp.status_code == 400
    assert "datatype" in resp.json()["detail"].lower()


def test_create_concept_invalid_class(client: TestClient) -> None:
    resp = client.post("/api/concepts", json={
        "name": "Bad", "datatype": "numeric", "concept_class": "invalid",
    }, headers=HEADERS)
    assert resp.status_code == 400
    assert "concept_class" in resp.json()["detail"].lower()


def test_list_concepts(client: TestClient) -> None:
    _create_concept(client, name="Concept A")
    _create_concept(client, name="Concept B")
    resp = client.get("/api/concepts", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_concept(client: TestClient) -> None:
    created = _create_concept(client)
    resp = client.get(f"/api/concepts/{created['id']}", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Concept"
    assert "answers" in data
    assert "mappings" in data


def test_get_concept_not_found(client: TestClient) -> None:
    resp = client.get("/api/concepts/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_concept(client: TestClient) -> None:
    created = _create_concept(client)
    resp = client.put(f"/api/concepts/{created['id']}", json={
        "name": "Updated Concept",
        "units": "kg",
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Concept"
    assert data["units"] == "kg"


def test_update_concept_not_found(client: TestClient) -> None:
    resp = client.put("/api/concepts/999", json={"name": "X"}, headers=HEADERS)
    assert resp.status_code == 404


def test_update_concept_invalid_datatype(client: TestClient) -> None:
    created = _create_concept(client)
    resp = client.put(f"/api/concepts/{created['id']}", json={
        "datatype": "bad",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_update_concept_no_fields(client: TestClient) -> None:
    created = _create_concept(client)
    resp = client.put(f"/api/concepts/{created['id']}", json={}, headers=HEADERS)
    assert resp.status_code == 400


# --- Retire / Unretire ---

def test_retire_concept(client: TestClient) -> None:
    created = _create_concept(client)
    resp = client.post(f"/api/concepts/{created['id']}/retire", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["retired"] == 1


def test_unretire_concept(client: TestClient) -> None:
    created = _create_concept(client)
    client.post(f"/api/concepts/{created['id']}/retire", headers=HEADERS)
    resp = client.post(f"/api/concepts/{created['id']}/unretire", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["retired"] == 0


def test_retired_excluded_from_list(client: TestClient) -> None:
    c1 = _create_concept(client, name="Active")
    c2 = _create_concept(client, name="Retired")
    client.post(f"/api/concepts/{c2['id']}/retire", headers=HEADERS)

    resp = client.get("/api/concepts", headers=HEADERS)
    names = [c["name"] for c in resp.json()]
    assert "Active" in names
    assert "Retired" not in names


def test_retired_included_when_requested(client: TestClient) -> None:
    c1 = _create_concept(client, name="Active")
    c2 = _create_concept(client, name="Retired")
    client.post(f"/api/concepts/{c2['id']}/retire", headers=HEADERS)

    resp = client.get("/api/concepts?include_retired=true", headers=HEADERS)
    names = [c["name"] for c in resp.json()]
    assert "Active" in names
    assert "Retired" in names


def test_retire_not_found(client: TestClient) -> None:
    resp = client.post("/api/concepts/999/retire", headers=HEADERS)
    assert resp.status_code == 404


# --- Concept Answers ---

def test_add_answer(client: TestClient) -> None:
    coded = _create_concept(client, name="Blood Type", datatype="coded")
    answer = _create_concept(client, name="A+", datatype="text", concept_class="misc")

    resp = client.post(f"/api/concepts/{coded['id']}/answers", json={
        "answer_concept_id": answer["id"],
        "sort_order": 0,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["answer_concept_id"] == answer["id"]


def test_add_answer_non_coded(client: TestClient) -> None:
    numeric = _create_concept(client, name="Temperature", datatype="numeric")
    answer = _create_concept(client, name="A+", datatype="text", concept_class="misc")

    resp = client.post(f"/api/concepts/{numeric['id']}/answers", json={
        "answer_concept_id": answer["id"],
    }, headers=HEADERS)
    assert resp.status_code == 400
    assert "coded" in resp.json()["detail"].lower()


def test_add_answer_concept_not_found(client: TestClient) -> None:
    coded = _create_concept(client, name="BT", datatype="coded")
    resp = client.post(f"/api/concepts/{coded['id']}/answers", json={
        "answer_concept_id": 999,
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_list_answers(client: TestClient) -> None:
    coded = _create_concept(client, name="Blood Type", datatype="coded")
    a1 = _create_concept(client, name="A+", datatype="text", concept_class="misc")
    a2 = _create_concept(client, name="B+", datatype="text", concept_class="misc")
    client.post(f"/api/concepts/{coded['id']}/answers", json={
        "answer_concept_id": a1["id"], "sort_order": 0,
    }, headers=HEADERS)
    client.post(f"/api/concepts/{coded['id']}/answers", json={
        "answer_concept_id": a2["id"], "sort_order": 1,
    }, headers=HEADERS)

    resp = client.get(f"/api/concepts/{coded['id']}/answers", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_answer(client: TestClient) -> None:
    coded = _create_concept(client, name="BT", datatype="coded")
    ans = _create_concept(client, name="O+", datatype="text", concept_class="misc")
    resp = client.post(f"/api/concepts/{coded['id']}/answers", json={
        "answer_concept_id": ans["id"],
    }, headers=HEADERS)
    answer_id = resp.json()["id"]

    resp = client.delete(f"/api/concepts/{coded['id']}/answers/{answer_id}", headers=HEADERS)
    assert resp.status_code == 204


# --- Concept Mappings ---

def test_create_mapping(client: TestClient) -> None:
    concept = _create_concept(client, name="Hypertension", concept_class="diagnosis")
    resp = client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "icd10",
        "code": "I10",
        "name": "Essential hypertension",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["source"] == "icd10"
    assert data["code"] == "I10"


def test_create_mapping_invalid_source(client: TestClient) -> None:
    concept = _create_concept(client)
    resp = client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "invalid",
        "code": "X",
    }, headers=HEADERS)
    assert resp.status_code == 400


def test_create_mapping_concept_not_found(client: TestClient) -> None:
    resp = client.post("/api/concepts/999/mappings", json={
        "source": "icd10", "code": "X",
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_list_mappings(client: TestClient) -> None:
    concept = _create_concept(client)
    client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "icd10", "code": "I10",
    }, headers=HEADERS)
    client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "snomed", "code": "38341003",
    }, headers=HEADERS)

    resp = client.get(f"/api/concepts/{concept['id']}/mappings", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_mapping(client: TestClient) -> None:
    concept = _create_concept(client)
    resp = client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "icd10", "code": "I10",
    }, headers=HEADERS)
    mapping_id = resp.json()["id"]

    resp = client.put(f"/api/concepts/{concept['id']}/mappings/{mapping_id}", json={
        "code": "I11",
        "name": "Updated",
    }, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["code"] == "I11"
    assert resp.json()["name"] == "Updated"


def test_delete_mapping(client: TestClient) -> None:
    concept = _create_concept(client)
    resp = client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "loinc", "code": "12345-6",
    }, headers=HEADERS)
    mapping_id = resp.json()["id"]

    resp = client.delete(f"/api/concepts/{concept['id']}/mappings/{mapping_id}", headers=HEADERS)
    assert resp.status_code == 204


# --- Concept Sets ---

def test_create_set(client: TestClient) -> None:
    resp = client.post("/api/sets", json={
        "name": "Vital Signs",
        "description": "Standard vital sign measurements",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Vital Signs"
    assert "members" in data


def test_list_sets(client: TestClient) -> None:
    client.post("/api/sets", json={"name": "Set A"}, headers=HEADERS)
    client.post("/api/sets", json={"name": "Set B"}, headers=HEADERS)
    resp = client.get("/api/sets", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_set(client: TestClient) -> None:
    resp = client.post("/api/sets", json={"name": "Test Set"}, headers=HEADERS)
    set_id = resp.json()["id"]
    resp = client.get(f"/api/sets/{set_id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Set"


def test_get_set_not_found(client: TestClient) -> None:
    resp = client.get("/api/sets/999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_set(client: TestClient) -> None:
    resp = client.post("/api/sets", json={"name": "Old Name"}, headers=HEADERS)
    set_id = resp.json()["id"]
    resp = client.put(f"/api/sets/{set_id}", json={"name": "New Name"}, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_set(client: TestClient) -> None:
    resp = client.post("/api/sets", json={"name": "Delete Me"}, headers=HEADERS)
    set_id = resp.json()["id"]
    resp = client.delete(f"/api/sets/{set_id}", headers=HEADERS)
    assert resp.status_code == 204
    resp = client.get(f"/api/sets/{set_id}", headers=HEADERS)
    assert resp.status_code == 404


# --- Set Members ---

def test_add_member(client: TestClient) -> None:
    concept = _create_concept(client, name="Temperature")
    resp = client.post("/api/sets", json={"name": "Vitals"}, headers=HEADERS)
    set_id = resp.json()["id"]

    resp = client.post(f"/api/sets/{set_id}/members", json={
        "concept_id": concept["id"],
        "sort_order": 0,
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["concept_name"] == "Temperature"


def test_add_member_concept_not_found(client: TestClient) -> None:
    resp = client.post("/api/sets", json={"name": "S"}, headers=HEADERS)
    set_id = resp.json()["id"]
    resp = client.post(f"/api/sets/{set_id}/members", json={
        "concept_id": 999,
    }, headers=HEADERS)
    assert resp.status_code == 404


def test_list_members(client: TestClient) -> None:
    c1 = _create_concept(client, name="Temp")
    c2 = _create_concept(client, name="Pulse")
    resp = client.post("/api/sets", json={"name": "Vitals"}, headers=HEADERS)
    set_id = resp.json()["id"]
    client.post(f"/api/sets/{set_id}/members", json={"concept_id": c1["id"], "sort_order": 0}, headers=HEADERS)
    client.post(f"/api/sets/{set_id}/members", json={"concept_id": c2["id"], "sort_order": 1}, headers=HEADERS)

    resp = client.get(f"/api/sets/{set_id}/members", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_remove_member(client: TestClient) -> None:
    concept = _create_concept(client, name="Temp")
    resp = client.post("/api/sets", json={"name": "Vitals"}, headers=HEADERS)
    set_id = resp.json()["id"]
    resp = client.post(f"/api/sets/{set_id}/members", json={
        "concept_id": concept["id"],
    }, headers=HEADERS)
    member_id = resp.json()["id"]

    resp = client.delete(f"/api/sets/{set_id}/members/{member_id}", headers=HEADERS)
    assert resp.status_code == 204


# --- Search ---

def test_search_by_name(client: TestClient) -> None:
    _create_concept(client, name="Temperature")
    _create_concept(client, name="Heart Rate")
    resp = client.get("/api/concepts/search?q=Temp", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "Temperature"


def test_search_by_class(client: TestClient) -> None:
    _create_concept(client, name="HTN", concept_class="diagnosis")
    _create_concept(client, name="Temp", concept_class="finding")
    resp = client.get("/api/concepts/search?class=diagnosis", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["concept_class"] == "diagnosis"


def test_search_by_source(client: TestClient) -> None:
    concept = _create_concept(client, name="HTN", concept_class="diagnosis")
    client.post(f"/api/concepts/{concept['id']}/mappings", json={
        "source": "icd10", "code": "I10",
    }, headers=HEADERS)
    _create_concept(client, name="Temp")

    resp = client.get("/api/concepts/search?source=icd10", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "HTN"


def test_search_combined(client: TestClient) -> None:
    c1 = _create_concept(client, name="HTN", concept_class="diagnosis")
    client.post(f"/api/concepts/{c1['id']}/mappings", json={
        "source": "icd10", "code": "I10",
    }, headers=HEADERS)
    c2 = _create_concept(client, name="DM2", concept_class="diagnosis")
    client.post(f"/api/concepts/{c2['id']}/mappings", json={
        "source": "icd10", "code": "E11",
    }, headers=HEADERS)

    resp = client.get("/api/concepts/search?q=HTN&source=icd10", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "HTN"


def test_search_no_results(client: TestClient) -> None:
    resp = client.get("/api/concepts/search?q=nonexistent", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# --- Seed Data ---

def test_seed_data_loads(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/concepts", headers=HEADERS)
    assert resp.status_code == 200
    concepts = resp.json()
    names = [c["name"] for c in concepts]
    assert "Temperature" in names
    assert "Hypertension" in names
    assert "Blood Glucose" in names
    assert "Antibiotic" in names
    assert "Blood Type" in names


def test_seed_vital_signs_set(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/sets", headers=HEADERS)
    assert resp.status_code == 200
    sets = resp.json()
    vital_sets = [s for s in sets if s["name"] == "Vital Signs"]
    assert len(vital_sets) == 1

    resp = seeded_client.get(f"/api/sets/{vital_sets[0]['id']}", headers=HEADERS)
    data = resp.json()
    assert len(data["members"]) == 9  # 9 vital sign concepts


def test_seed_blood_type_answers(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/concepts/search?q=Blood+Type", headers=HEADERS)
    bt_concepts = [c for c in resp.json() if c["name"] == "Blood Type"]
    assert len(bt_concepts) == 1

    resp = seeded_client.get(f"/api/concepts/{bt_concepts[0]['id']}", headers=HEADERS)
    data = resp.json()
    assert len(data["answers"]) == 8  # A+, A-, B+, B-, AB+, AB-, O+, O-


def test_seed_icd10_mappings(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/concepts/search?source=icd10", headers=HEADERS)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 10  # 10 diagnoses have ICD-10 mappings
