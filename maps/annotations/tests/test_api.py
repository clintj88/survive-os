"""Tests for the Map Annotations API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import init_db, query, set_db_path
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
    """Client with sample layers and annotations."""
    client.post("/api/layers", json={
        "name": "Water Sources",
        "type": "resource_locations",
        "color": "#4fc3f7",
    })
    client.post("/api/layers", json={
        "name": "Hazard Zones",
        "type": "hazard_zones",
        "color": "#ff4757",
    })
    client.post("/api/layers", json={
        "name": "Mesh Network",
        "type": "mesh_nodes",
        "color": "#9e9e9e",
    })
    # Annotations
    client.post("/api/annotations", json={
        "layer_id": 1,
        "geometry": {"type": "Point", "coordinates": [-73.935, 40.730]},
        "category": "water_source",
        "title": "Well Alpha",
        "description": "Deep well, clean water",
        "creator": "scout1",
        "latitude": 40.730,
        "longitude": -73.935,
    })
    client.post("/api/annotations", json={
        "layer_id": 2,
        "geometry": {"type": "Polygon", "coordinates": [[[-73.94, 40.73], [-73.93, 40.73], [-73.93, 40.74], [-73.94, 40.74], [-73.94, 40.73]]]},
        "category": "contamination",
        "title": "Chemical Spill Zone",
        "creator": "recon",
        "latitude": 40.735,
        "longitude": -73.935,
    })
    client.post("/api/annotations", json={
        "layer_id": 3,
        "geometry": {"type": "Point", "coordinates": [-73.940, 40.725]},
        "category": "meshtastic_node",
        "title": "Node Bravo",
        "creator": "comms",
        "radius_meters": 500.0,
        "latitude": 40.725,
        "longitude": -73.940,
    })
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Layers ---

def test_create_layer(client: TestClient) -> None:
    resp = client.post("/api/layers", json={
        "name": "Supply Depots",
        "type": "resource_locations",
        "color": "#00ff00",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Supply Depots"
    assert data["type"] == "resource_locations"
    assert data["color"] == "#00ff00"
    assert data["visible"] is True


def test_create_layer_invalid_type(client: TestClient) -> None:
    resp = client.post("/api/layers", json={
        "name": "Bad Layer",
        "type": "invalid_type",
    })
    assert resp.status_code == 400


def test_list_layers(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/layers")
    assert resp.status_code == 200
    layers = resp.json()
    assert len(layers) == 3


def test_list_layers_with_annotation_count(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/layers")
    layers = resp.json()
    water = next(l for l in layers if l["name"] == "Water Sources")
    assert water["annotation_count"] == 1


def test_get_layer(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/layers/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Water Sources"


def test_get_layer_not_found(client: TestClient) -> None:
    resp = client.get("/api/layers/999")
    assert resp.status_code == 404


def test_update_layer(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/layers/1", json={"name": "Fresh Water", "visible": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Fresh Water"
    assert data["visible"] is False


def test_update_layer_invalid_type(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/layers/1", json={"type": "bad_type"})
    assert resp.status_code == 400


def test_delete_layer(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/layers/1")
    assert resp.status_code == 200
    # Layer gone
    resp = seeded_client.get("/api/layers/1")
    assert resp.status_code == 404
    # Annotations in that layer also deleted
    resp = seeded_client.get("/api/annotations?layer_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_delete_layer_not_found(client: TestClient) -> None:
    resp = client.delete("/api/layers/999")
    assert resp.status_code == 404


# --- Annotations ---

def test_create_annotation(client: TestClient) -> None:
    client.post("/api/layers", json={"name": "Test", "type": "resource_locations"})
    resp = client.post("/api/annotations", json={
        "layer_id": 1,
        "geometry": {"type": "Point", "coordinates": [-73.9, 40.7]},
        "category": "fuel_cache",
        "title": "Fuel Depot A",
        "creator": "logistics",
        "latitude": 40.7,
        "longitude": -73.9,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Fuel Depot A"
    assert data["category"] == "fuel_cache"
    assert data["crdt_id"] is not None
    assert data["geometry"]["type"] == "Point"


def test_create_annotation_invalid_category(client: TestClient) -> None:
    client.post("/api/layers", json={"name": "Test", "type": "resource_locations"})
    resp = client.post("/api/annotations", json={
        "layer_id": 1,
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "category": "invalid_cat",
    })
    assert resp.status_code == 400


def test_create_annotation_invalid_layer(client: TestClient) -> None:
    resp = client.post("/api/annotations", json={
        "layer_id": 999,
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "category": "water_source",
    })
    assert resp.status_code == 404


def test_list_annotations(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_list_annotations_filter_layer(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations?layer_id=1")
    assert resp.status_code == 200
    anns = resp.json()
    assert len(anns) == 1
    assert anns[0]["title"] == "Well Alpha"


def test_get_annotation(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations/1")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Well Alpha"


def test_get_annotation_not_found(client: TestClient) -> None:
    resp = client.get("/api/annotations/999")
    assert resp.status_code == 404


def test_update_annotation(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/annotations/1", json={
        "title": "Well Alpha (verified)",
        "properties": {"tested": True},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Well Alpha (verified)"
    assert data["properties"]["tested"] is True


def test_update_annotation_invalid_category(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/annotations/1", json={"category": "bad_cat"})
    assert resp.status_code == 400


def test_delete_annotation(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/annotations/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/annotations/1")
    assert resp.status_code == 404


def test_delete_annotation_not_found(client: TestClient) -> None:
    resp = client.delete("/api/annotations/999")
    assert resp.status_code == 404


# --- Bounding Box Search ---

def test_bbox_search(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations/search?min_lat=40.72&min_lng=-73.95&max_lat=40.74&max_lng=-73.92")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 2  # Well Alpha and Chemical Spill Zone


def test_bbox_search_no_results(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations/search?min_lat=0&min_lng=0&max_lat=1&max_lng=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# --- Meshtastic Node Coverage ---

def test_meshtastic_node_radius(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations/3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "meshtastic_node"
    assert data["radius_meters"] == 500.0


# --- GeoJSON Export ---

def test_geojson_export(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/geojson/export?layer_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["properties"]["title"] == "Well Alpha"
    assert feature["properties"]["crdt_id"] is not None


def test_geojson_export_not_found(client: TestClient) -> None:
    resp = client.get("/api/geojson/export?layer_id=999")
    assert resp.status_code == 404


# --- GeoJSON Import ---

def test_geojson_import(seeded_client: TestClient) -> None:
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-73.95, 40.71]},
                "properties": {
                    "category": "supply_depot",
                    "title": "Depot Charlie",
                    "creator": "logistics",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[-73.95, 40.71], [-73.94, 40.72]]},
                "properties": {
                    "category": "trade_route",
                    "title": "Route Delta",
                },
            },
        ],
    }
    resp = seeded_client.post("/api/geojson/import?layer_id=1", json=feature_collection)
    assert resp.status_code == 201
    data = resp.json()
    assert data["imported"] == 2
    assert len(data["errors"]) == 0

    # Verify imported annotations exist
    resp = seeded_client.get("/api/annotations?layer_id=1")
    anns = resp.json()
    assert len(anns) == 3  # 1 original + 2 imported


def test_geojson_import_with_errors(seeded_client: TestClient) -> None:
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-73.95, 40.71]},
                "properties": {"category": "water_source", "title": "Good"},
            },
            {
                "type": "Feature",
                "properties": {"title": "Missing geometry"},
            },
        ],
    }
    resp = seeded_client.post("/api/geojson/import?layer_id=1", json=feature_collection)
    assert resp.status_code == 201
    data = resp.json()
    assert data["imported"] == 1
    assert len(data["errors"]) == 1


def test_geojson_import_layer_not_found(client: TestClient) -> None:
    resp = client.post("/api/geojson/import?layer_id=999", json={
        "type": "FeatureCollection",
        "features": [],
    })
    assert resp.status_code == 404


def test_geojson_import_extracts_lat_lng_from_point(seeded_client: TestClient) -> None:
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-73.95, 40.71]},
            "properties": {"category": "water_source", "title": "Auto Coords"},
        }],
    }
    seeded_client.post("/api/geojson/import?layer_id=1", json=feature_collection)
    resp = seeded_client.get("/api/annotations?layer_id=1")
    imported = [a for a in resp.json() if a["title"] == "Auto Coords"]
    assert len(imported) == 1
    assert imported[0]["latitude"] == 40.71
    assert imported[0]["longitude"] == -73.95


# --- CRDT ID ---

def test_annotation_has_crdt_id(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations/1")
    data = resp.json()
    assert data["crdt_id"] is not None
    assert len(data["crdt_id"]) > 0


def test_crdt_id_unique(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/annotations")
    anns = resp.json()
    crdt_ids = [a["crdt_id"] for a in anns]
    assert len(crdt_ids) == len(set(crdt_ids))
