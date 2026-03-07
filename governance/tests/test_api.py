"""Comprehensive tests for the SURVIVE OS Governance module."""

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()
    yield


client = TestClient(app)


# --- Health ---

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


# --- Census ---

def _create_person(name="Alice", **kwargs):
    payload = {"name": name, "dob": "1990-01-15", "sex": "F", "occupation": "farmer", **kwargs}
    return client.post("/api/census/persons", json=payload)


def test_create_person():
    r = _create_person()
    assert r.status_code == 201
    assert r.json()["name"] == "Alice"


def test_list_persons():
    _create_person("Alice")
    _create_person("Bob", sex="M")
    r = client.get("/api/census/persons")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_search_persons():
    _create_person("Alice")
    _create_person("Bob", sex="M")
    r = client.get("/api/census/persons?search=Ali")
    assert len(r.json()) == 1


def test_get_person():
    create = _create_person()
    pid = create.json()["id"]
    r = client.get(f"/api/census/persons/{pid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"


def test_get_person_not_found():
    r = client.get("/api/census/persons/999")
    assert r.status_code == 404


def test_update_person():
    pid = _create_person().json()["id"]
    r = client.put(f"/api/census/persons/{pid}", json={"occupation": "teacher"})
    assert r.status_code == 200
    assert r.json()["occupation"] == "teacher"


def test_update_person_no_fields():
    pid = _create_person().json()["id"]
    r = client.put(f"/api/census/persons/{pid}", json={})
    assert r.status_code == 400


def test_set_skill():
    pid = _create_person().json()["id"]
    r = client.post(f"/api/census/persons/{pid}/skills", json={"category": "farming", "rating": 4})
    assert r.status_code == 201
    skills = r.json()["skills"]
    assert any(s["category"] == "farming" and s["rating"] == 4 for s in skills)


def test_population_stats():
    _create_person("Alice")
    _create_person("Bob", sex="M")
    r = client.get("/api/census/stats")
    assert r.status_code == 200
    assert r.json()["total_active"] == 2


def test_filter_by_status():
    pid = _create_person().json()["id"]
    client.put(f"/api/census/persons/{pid}", json={"status": "departed"})
    r = client.get("/api/census/persons?status=active")
    assert len(r.json()) == 0


# --- Voting ---

def _create_ballot(**kwargs):
    payload = {
        "title": "Test Vote",
        "description": "A test ballot",
        "ballot_type": "yes_no",
        "options": ["yes", "no"],
        "voting_period_end": "2026-12-31T23:59:59",
        "created_by": "admin",
        **kwargs,
    }
    return client.post("/api/voting/ballots", json=payload)


def test_create_ballot():
    r = _create_ballot()
    assert r.status_code == 201
    assert r.json()["title"] == "Test Vote"


def test_list_ballots():
    _create_ballot()
    r = client.get("/api/voting/ballots")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_cast_vote():
    bid = _create_ballot().json()["id"]
    pid = _create_person().json()["id"]
    r = client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "yes"})
    assert r.status_code == 201


def test_duplicate_vote():
    bid = _create_ballot().json()["id"]
    pid = _create_person().json()["id"]
    client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "yes"})
    r = client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "no"})
    assert r.status_code == 409


def test_invalid_choice():
    bid = _create_ballot().json()["id"]
    pid = _create_person().json()["id"]
    r = client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "maybe"})
    assert r.status_code == 400


def test_vote_results():
    bid = _create_ballot().json()["id"]
    p1 = _create_person("Voter1").json()["id"]
    p2 = _create_person("Voter2").json()["id"]
    client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": p1, "choice": "yes"})
    client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": p2, "choice": "no"})
    r = client.get(f"/api/voting/ballots/{bid}/results")
    assert r.status_code == 200
    assert r.json()["total_votes"] == 2
    assert r.json()["tally"]["yes"] == 1
    assert r.json()["tally"]["no"] == 1


def test_audit_log():
    bid = _create_ballot().json()["id"]
    pid = _create_person().json()["id"]
    client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "yes"})
    r = client.get(f"/api/voting/ballots/{bid}/audit")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["action"] == "vote_cast"


def test_ranked_choice_vote():
    bid = _create_ballot(
        title="Ranked", ballot_type="ranked_choice", options=["a", "b", "c"]
    ).json()["id"]
    pid = _create_person().json()["id"]
    r = client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "b,a,c"})
    assert r.status_code == 201


def test_ranked_choice_invalid():
    bid = _create_ballot(
        title="Ranked2", ballot_type="ranked_choice", options=["a", "b", "c"]
    ).json()["id"]
    pid = _create_person().json()["id"]
    r = client.post(f"/api/voting/ballots/{bid}/vote", json={"voter_id": pid, "choice": "z,a,b"})
    assert r.status_code == 400


# --- Resources ---

def _create_resource(**kwargs):
    payload = {"category": "food", "name": "Rice", "quantity": 100, "unit": "kg", "low_threshold": 10, **kwargs}
    return client.post("/api/resources/inventory", json=payload)


def test_create_resource():
    r = _create_resource()
    assert r.status_code == 201
    assert r.json()["name"] == "Rice"


def test_list_inventory():
    _create_resource()
    r = client.get("/api/resources/inventory")
    assert len(r.json()) >= 1


def test_filter_inventory_by_category():
    _create_resource(category="food", name="Rice")
    _create_resource(category="water", name="Purified Water")
    r = client.get("/api/resources/inventory?category=water")
    assert all(i["category"] == "water" for i in r.json())


def test_update_resource():
    rid = _create_resource().json()["id"]
    r = client.put(f"/api/resources/inventory/{rid}", json={"quantity": 50})
    assert r.json()["quantity"] == 50


def test_distribute_resource():
    rid = _create_resource(quantity=100).json()["id"]
    pid = _create_person().json()["id"]
    r = client.post("/api/resources/distribute", json={"resource_id": rid, "person_id": pid, "quantity": 5})
    assert r.status_code == 201
    updated = client.get(f"/api/resources/inventory/{rid}").json()
    assert updated["quantity"] == 95


def test_distribute_insufficient():
    rid = _create_resource(quantity=2).json()["id"]
    pid = _create_person().json()["id"]
    r = client.post("/api/resources/distribute", json={"resource_id": rid, "person_id": pid, "quantity": 10})
    assert r.status_code == 400


def test_ration_calculator():
    rid = _create_resource(quantity=100).json()["id"]
    _create_person("P1")
    _create_person("P2")
    r = client.post("/api/resources/ration-calculator", json={"resource_id": rid, "days": 7})
    assert r.status_code == 200
    data = r.json()
    assert data["population"] == 2
    assert data["per_person_total"] == 50.0


def test_low_resource_alerts():
    _create_resource(quantity=5, low_threshold=10, name="LowItem")
    r = client.get("/api/resources/alerts")
    assert len(r.json()) >= 1


def test_distribution_log():
    rid = _create_resource(quantity=100).json()["id"]
    pid = _create_person().json()["id"]
    client.post("/api/resources/distribute", json={"resource_id": rid, "person_id": pid, "quantity": 5})
    r = client.get(f"/api/resources/distribution-log?resource_id={rid}")
    assert len(r.json()) == 1


# --- Treaties ---

def _create_treaty(**kwargs):
    payload = {"title": "Peace Treaty", "parties": "Group A, Group B", "content": "Terms here.", **kwargs}
    return client.post("/api/treaties", json=payload)


def test_create_treaty():
    r = _create_treaty()
    assert r.status_code == 201
    assert r.json()["title"] == "Peace Treaty"


def test_list_treaties():
    _create_treaty()
    r = client.get("/api/treaties")
    assert len(r.json()) >= 1


def test_treaty_versioning():
    tid = _create_treaty().json()["id"]
    client.put(f"/api/treaties/{tid}", json={"content": "Updated terms.", "changed_by": "admin"})
    r = client.get(f"/api/treaties/{tid}/versions")
    assert len(r.json()) == 2


def test_treaty_signatories():
    tid = _create_treaty().json()["id"]
    r = client.post(f"/api/treaties/{tid}/signatories", json={"person_name": "Alice"})
    assert r.status_code == 201
    assert any(s["person_name"] == "Alice" for s in r.json()["signatories"])


def test_update_treaty_status():
    tid = _create_treaty().json()["id"]
    r = client.put(f"/api/treaties/{tid}", json={"status": "active"})
    assert r.json()["status"] == "active"


# --- Disputes ---

def _create_dispute(**kwargs):
    payload = {"parties": "Alice vs Bob", "description": "Land dispute", "category": "property", **kwargs}
    return client.post("/api/disputes", json=payload)


def test_create_dispute():
    r = _create_dispute()
    assert r.status_code == 201
    assert r.json()["status"] == "open"


def test_list_disputes():
    _create_dispute()
    r = client.get("/api/disputes")
    assert len(r.json()) >= 1


def test_filter_disputes():
    _create_dispute(category="property")
    _create_dispute(category="trade", parties="C vs D", description="Trade issue")
    r = client.get("/api/disputes?category=trade")
    assert all(d["category"] == "trade" for d in r.json())


def test_resolve_dispute():
    did = _create_dispute().json()["id"]
    r = client.put(f"/api/disputes/{did}", json={"status": "resolved", "outcome": "Land split"})
    assert r.json()["status"] == "resolved"
    assert r.json()["outcome"] == "Land split"


def test_precedent_linking():
    d1 = _create_dispute().json()["id"]
    client.put(f"/api/disputes/{d1}", json={"status": "resolved", "outcome": "Shared"})
    d2 = _create_dispute(parties="E vs F", description="Similar dispute").json()["id"]
    r = client.put(f"/api/disputes/{d2}", json={"precedent_id": d1})
    assert r.json()["precedent_id"] == d1


# --- Duties ---

def test_create_assignment():
    pid = _create_person().json()["id"]
    r = client.post("/api/duties/assignments", json={"person_id": pid, "duty_type": "watch", "duty_date": "2026-03-10", "shift": "night"})
    assert r.status_code == 201
    assert r.json()["duty_type"] == "watch"


def test_list_assignments():
    pid = _create_person().json()["id"]
    client.post("/api/duties/assignments", json={"person_id": pid, "duty_type": "cooking", "duty_date": "2026-03-10", "shift": "morning"})
    r = client.get("/api/duties/assignments?duty_date=2026-03-10")
    assert len(r.json()) >= 1


def test_fairness_report():
    pid = _create_person().json()["id"]
    client.post("/api/duties/assignments", json={"person_id": pid, "duty_type": "watch", "duty_date": "2026-03-10", "shift": "morning"})
    client.post("/api/duties/assignments", json={"person_id": pid, "duty_type": "watch", "duty_date": "2026-03-11", "shift": "morning"})
    r = client.get("/api/duties/fairness")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_swap_request():
    p1 = _create_person("SwapA").json()["id"]
    p2 = _create_person("SwapB").json()["id"]
    aid = client.post("/api/duties/assignments", json={"person_id": p1, "duty_type": "watch", "duty_date": "2026-03-15", "shift": "morning"}).json()["id"]
    r = client.post("/api/duties/swap-requests", json={"assignment_id": aid, "requester_id": p1, "target_id": p2})
    assert r.status_code == 201
    sid = r.json()["id"]
    r2 = client.put(f"/api/duties/swap-requests/{sid}/approve")
    assert r2.json()["status"] == "approved"


def test_generate_weekly():
    _create_person("W1")
    _create_person("W2")
    r = client.post("/api/duties/generate-weekly?start_date=2026-03-09&duty_type=watch")
    assert r.status_code == 200
    assert len(r.json()) == 21  # 7 days * 3 shifts


# --- Journal ---

def test_create_journal_entry():
    r = client.post("/api/journal/entries", json={"title": "Day 1", "content": "We arrived.", "author": "Scribe"})
    assert r.status_code == 201
    assert r.json()["title"] == "Day 1"


def test_list_journal_entries():
    client.post("/api/journal/entries", json={"title": "Entry", "content": "Text", "author": "A"})
    r = client.get("/api/journal/entries")
    assert len(r.json()) >= 1


def test_filter_journal_by_category():
    client.post("/api/journal/entries", json={"title": "E1", "content": "T", "author": "A", "category": "milestone"})
    client.post("/api/journal/entries", json={"title": "E2", "content": "T", "author": "A", "category": "daily_log"})
    r = client.get("/api/journal/entries?category=milestone")
    assert all(e["category"] == "milestone" for e in r.json())


# --- Registry ---

def test_create_birth():
    r = client.post("/api/registry/births", json={"child_name": "Baby", "dob": "2026-01-01", "parent1": "Alice", "parent2": "Bob"})
    assert r.status_code == 201
    assert r.json()["child_name"] == "Baby"


def test_list_births():
    client.post("/api/registry/births", json={"child_name": "Baby", "dob": "2026-01-01"})
    r = client.get("/api/registry/births")
    assert len(r.json()) >= 1


def test_create_death():
    r = client.post("/api/registry/deaths", json={"person_name": "Elder", "date_of_death": "2026-02-01", "cause": "natural"})
    assert r.status_code == 201


def test_list_deaths():
    client.post("/api/registry/deaths", json={"person_name": "Elder", "date_of_death": "2026-02-01"})
    r = client.get("/api/registry/deaths")
    assert len(r.json()) >= 1


def test_create_marriage():
    r = client.post("/api/registry/marriages", json={"party1": "Alice", "party2": "Bob", "marriage_date": "2026-06-15", "officiant": "Mayor"})
    assert r.status_code == 201


def test_list_marriages():
    client.post("/api/registry/marriages", json={"party1": "A", "party2": "B", "marriage_date": "2026-06-15"})
    r = client.get("/api/registry/marriages")
    assert len(r.json()) >= 1


# --- Calendar ---

def _create_event(**kwargs):
    payload = {"title": "Town Meeting", "event_date": "2026-03-15", "event_type": "meeting", **kwargs}
    return client.post("/api/calendar/events", json=payload)


def test_create_event():
    r = _create_event()
    assert r.status_code == 201
    assert r.json()["title"] == "Town Meeting"


def test_list_events():
    _create_event()
    r = client.get("/api/calendar/events")
    assert len(r.json()) >= 1


def test_filter_events_by_month():
    _create_event(event_date="2026-03-15")
    _create_event(title="April Event", event_date="2026-04-10")
    r = client.get("/api/calendar/events?month=2026-03")
    assert all("2026-03" in e["event_date"] for e in r.json())


def test_filter_events_by_type():
    _create_event(event_type="meeting")
    _create_event(title="Party", event_type="celebration", event_date="2026-03-20")
    r = client.get("/api/calendar/events?event_type=celebration")
    assert all(e["event_type"] == "celebration" for e in r.json())


def test_upcoming_events():
    _create_event(event_date="2099-01-01")
    r = client.get("/api/calendar/upcoming?days=30000")
    assert len(r.json()) >= 1
