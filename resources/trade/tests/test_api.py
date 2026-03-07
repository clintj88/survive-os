"""Tests for the Trade & Barter Ledger API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import execute, init_db, set_db_path
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    set_db_path(db_path)
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_trade(client: TestClient) -> dict:
    return client.post("/api/trades", json={
        "party_a": "Alice",
        "party_b": "Bob",
        "description": "Wheat for eggs",
        "items": [
            {"side": "give", "item_description": "Wheat", "quantity": 10, "unit": "kg", "value_in_labor_hours": 5.0},
            {"side": "receive", "item_description": "Eggs", "quantity": 24, "unit": "count", "value_in_labor_hours": 5.0},
        ],
    }).json()


# Health

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# Ledger

def test_create_trade(client: TestClient) -> None:
    resp = client.post("/api/trades", json={
        "party_a": "Alice",
        "party_b": "Bob",
        "description": "Wheat for eggs",
        "items": [
            {"side": "give", "item_description": "Wheat", "quantity": 10, "unit": "kg", "value_in_labor_hours": 5.0},
            {"side": "receive", "item_description": "Eggs", "quantity": 24, "unit": "count", "value_in_labor_hours": 5.0},
        ],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["party_a"] == "Alice"
    assert data["party_b"] == "Bob"
    assert len(data["items"]) == 2
    assert data["status"] == "pending"


def test_create_trade_requires_both_sides(client: TestClient) -> None:
    resp = client.post("/api/trades", json={
        "party_a": "Alice",
        "party_b": "Bob",
        "items": [
            {"side": "give", "item_description": "Wheat", "quantity": 10, "unit": "kg"},
        ],
    })
    assert resp.status_code == 400


def test_create_trade_requires_items(client: TestClient) -> None:
    resp = client.post("/api/trades", json={
        "party_a": "Alice",
        "party_b": "Bob",
        "items": [],
    })
    assert resp.status_code == 400


def test_list_trades(client: TestClient) -> None:
    _create_trade(client)
    resp = client.get("/api/trades")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_trades_filter_party(client: TestClient) -> None:
    _create_trade(client)
    resp = client.get("/api/trades?party=Alice")
    assert len(resp.json()) == 1
    resp = client.get("/api/trades?party=Charlie")
    assert len(resp.json()) == 0


def test_get_trade(client: TestClient) -> None:
    trade = _create_trade(client)
    resp = client.get(f"/api/trades/{trade['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == trade["id"]


def test_get_trade_not_found(client: TestClient) -> None:
    resp = client.get("/api/trades/999")
    assert resp.status_code == 404


def test_update_trade_status(client: TestClient) -> None:
    trade = _create_trade(client)
    resp = client.patch(f"/api/trades/{trade['id']}/status", json={"status": "completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_update_trade_invalid_status(client: TestClient) -> None:
    trade = _create_trade(client)
    resp = client.patch(f"/api/trades/{trade['id']}/status", json={"status": "invalid"})
    assert resp.status_code == 400


def test_validate_trade_balanced(client: TestClient) -> None:
    trade = _create_trade(client)
    resp = client.get(f"/api/trades/{trade['id']}/validate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balanced"] is True
    assert data["give_total_hours"] == 5.0
    assert data["receive_total_hours"] == 5.0


def test_validate_trade_unbalanced(client: TestClient) -> None:
    resp = client.post("/api/trades", json={
        "party_a": "Alice",
        "party_b": "Bob",
        "items": [
            {"side": "give", "item_description": "Wheat", "quantity": 10, "unit": "kg", "value_in_labor_hours": 5.0},
            {"side": "receive", "item_description": "Eggs", "quantity": 6, "unit": "count", "value_in_labor_hours": 2.0},
        ],
    })
    trade = resp.json()
    resp = client.get(f"/api/trades/{trade['id']}/validate")
    data = resp.json()
    assert data["balanced"] is False


# Rates

def test_create_rate(client: TestClient) -> None:
    resp = client.post("/api/rates", json={
        "commodity_a": "kg_wheat",
        "commodity_b": "labor_hours",
        "rate": 0.5,
        "set_by": "council",
    })
    assert resp.status_code == 201
    assert resp.json()["rate"] == 0.5


def test_create_rate_must_be_positive(client: TestClient) -> None:
    resp = client.post("/api/rates", json={
        "commodity_a": "kg_wheat",
        "commodity_b": "labor_hours",
        "rate": -1,
    })
    assert resp.status_code == 400


def test_list_rates(client: TestClient) -> None:
    client.post("/api/rates", json={
        "commodity_a": "kg_wheat",
        "commodity_b": "labor_hours",
        "rate": 0.5,
    })
    resp = client.get("/api/rates")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_current_rates(client: TestClient) -> None:
    client.post("/api/rates", json={"commodity_a": "kg_wheat", "commodity_b": "labor_hours", "rate": 0.5})
    client.post("/api/rates", json={"commodity_a": "kg_wheat", "commodity_b": "labor_hours", "rate": 0.6})
    resp = client.get("/api/rates/current")
    assert resp.status_code == 200
    rates = resp.json()
    wheat_rate = [r for r in rates if r["commodity_a"] == "kg_wheat"]
    assert len(wheat_rate) == 1
    assert wheat_rate[0]["rate"] == 0.6


def test_rate_history(client: TestClient) -> None:
    client.post("/api/rates", json={"commodity_a": "kg_wheat", "commodity_b": "labor_hours", "rate": 0.5})
    client.post("/api/rates", json={"commodity_a": "kg_wheat", "commodity_b": "labor_hours", "rate": 0.6})
    resp = client.get("/api/rates/history/kg_wheat/labor_hours")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_convert(client: TestClient) -> None:
    client.post("/api/rates", json={"commodity_a": "kg_wheat", "commodity_b": "labor_hours", "rate": 0.5})
    resp = client.get("/api/rates/convert/kg_wheat/labor_hours?amount=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == 5.0


def test_convert_not_found(client: TestClient) -> None:
    resp = client.get("/api/rates/convert/gold/labor_hours")
    assert resp.status_code == 404


# History

def test_person_history(client: TestClient) -> None:
    _create_trade(client)
    resp = client.get("/api/history/person/Alice")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_balance_between(client: TestClient) -> None:
    trade = _create_trade(client)
    # Complete the trade
    client.patch(f"/api/trades/{trade['id']}/status", json={"status": "completed"})
    resp = client.get("/api/history/balance/Alice/Bob")
    assert resp.status_code == 200
    data = resp.json()
    assert data["a_gave_hours"] == 5.0


def test_trade_summary(client: TestClient) -> None:
    trade = _create_trade(client)
    client.patch(f"/api/trades/{trade['id']}/status", json={"status": "completed"})
    resp = client.get("/api/history/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_trades"] == 1
    assert data["completed"] == 1


# Market

def test_create_market_day(client: TestClient) -> None:
    resp = client.post("/api/market", json={
        "date": "2026-03-15",
        "location": "Town Square",
        "organizer": "Council",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["location"] == "Town Square"
    assert data["status"] == "upcoming"


def test_list_market_days(client: TestClient) -> None:
    client.post("/api/market", json={"date": "2026-03-15", "location": "Square", "organizer": "Bob"})
    resp = client.get("/api/market")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_market_day(client: TestClient) -> None:
    resp = client.post("/api/market", json={"date": "2026-03-15", "location": "Square", "organizer": "Bob"})
    market_id = resp.json()["id"]
    resp = client.patch(f"/api/market/{market_id}", json={"status": "active"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_update_market_day_invalid_status(client: TestClient) -> None:
    resp = client.post("/api/market", json={"date": "2026-03-15", "location": "Square", "organizer": "Bob"})
    market_id = resp.json()["id"]
    resp = client.patch(f"/api/market/{market_id}", json={"status": "invalid"})
    assert resp.status_code == 400


def test_add_listing(client: TestClient) -> None:
    resp = client.post("/api/market", json={"date": "2026-03-15", "location": "Square", "organizer": "Bob"})
    market_id = resp.json()["id"]
    resp = client.post(f"/api/market/{market_id}/listings", json={
        "person": "Alice",
        "item_description": "Fresh eggs",
        "quantity": 24,
        "unit": "count",
        "asking_price_hours": 2.0,
        "type": "offer",
    })
    assert resp.status_code == 201
    assert resp.json()["person"] == "Alice"


def test_list_listings(client: TestClient) -> None:
    resp = client.post("/api/market", json={"date": "2026-03-15", "location": "Square", "organizer": "Bob"})
    market_id = resp.json()["id"]
    client.post(f"/api/market/{market_id}/listings", json={
        "person": "Alice", "item_description": "Eggs", "quantity": 12, "unit": "count", "type": "offer",
    })
    client.post(f"/api/market/{market_id}/listings", json={
        "person": "Bob", "item_description": "Flour", "quantity": 5, "unit": "kg", "type": "want",
    })
    resp = client.get(f"/api/market/{market_id}/listings")
    assert len(resp.json()) == 2
    resp = client.get(f"/api/market/{market_id}/listings?type=offer")
    assert len(resp.json()) == 1


def test_market_day_not_found(client: TestClient) -> None:
    resp = client.get("/api/market/999")
    assert resp.status_code == 404


# Skills

def test_create_skill(client: TestClient) -> None:
    resp = client.post("/api/skills", json={
        "person_name": "Alice",
        "skill_category": "farming",
        "skill_name": "Crop rotation",
        "proficiency": "expert",
        "hourly_rate": 1.5,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["person_name"] == "Alice"
    assert data["proficiency"] == "expert"


def test_create_skill_invalid_category(client: TestClient) -> None:
    resp = client.post("/api/skills", json={
        "person_name": "Alice",
        "skill_category": "juggling",
        "skill_name": "Balls",
    })
    assert resp.status_code == 400


def test_create_skill_invalid_proficiency(client: TestClient) -> None:
    resp = client.post("/api/skills", json={
        "person_name": "Alice",
        "skill_category": "farming",
        "skill_name": "Planting",
        "proficiency": "godlike",
    })
    assert resp.status_code == 400


def test_list_skills(client: TestClient) -> None:
    client.post("/api/skills", json={
        "person_name": "Alice", "skill_category": "farming", "skill_name": "Planting",
    })
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_skills_filter(client: TestClient) -> None:
    client.post("/api/skills", json={
        "person_name": "Alice", "skill_category": "farming", "skill_name": "Planting",
    })
    client.post("/api/skills", json={
        "person_name": "Bob", "skill_category": "medical", "skill_name": "First aid",
    })
    resp = client.get("/api/skills?category=farming")
    assert len(resp.json()) == 1
    resp = client.get("/api/skills?person=Bob")
    assert len(resp.json()) == 1


def test_search_skills(client: TestClient) -> None:
    client.post("/api/skills", json={
        "person_name": "Alice", "skill_category": "farming", "skill_name": "Crop rotation",
    })
    resp = client.get("/api/skills/search?q=crop")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_skill(client: TestClient) -> None:
    resp = client.post("/api/skills", json={
        "person_name": "Alice", "skill_category": "farming", "skill_name": "Planting",
    })
    skill_id = resp.json()["id"]
    resp = client.put(f"/api/skills/{skill_id}", json={"proficiency": "expert", "hourly_rate": 2.0})
    assert resp.status_code == 200
    assert resp.json()["proficiency"] == "expert"
    assert resp.json()["hourly_rate"] == 2.0


def test_skill_categories(client: TestClient) -> None:
    resp = client.get("/api/skills/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert "farming" in cats
    assert "medical" in cats


def test_skill_not_found(client: TestClient) -> None:
    resp = client.get("/api/skills/999")
    assert resp.status_code == 404
