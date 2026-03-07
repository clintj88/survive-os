"""Tests for the Map Tile Server API."""

import gzip
import sqlite3
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


def _create_mbtiles(path: Path, tiles: list[tuple[int, int, int, bytes]] | None = None) -> str:
    """Create a minimal MBTiles file for testing."""
    path.mkdir(parents=True, exist_ok=True)
    filepath = str(path / "test.mbtiles")
    conn = sqlite3.connect(filepath)
    conn.execute("""
        CREATE TABLE tiles (
            zoom_level INTEGER,
            tile_column INTEGER,
            tile_row INTEGER,
            tile_data BLOB
        )
    """)
    conn.execute("""
        CREATE TABLE metadata (
            name TEXT,
            value TEXT
        )
    """)
    conn.execute("INSERT INTO metadata VALUES ('name', 'test')")
    conn.execute("INSERT INTO metadata VALUES ('format', 'pbf')")
    if tiles:
        conn.executemany(
            "INSERT INTO tiles VALUES (?, ?, ?, ?)", tiles
        )
    conn.commit()
    conn.close()
    return filepath


@pytest.fixture
def mbtiles_path(tmp_path: Path) -> str:
    return _create_mbtiles(tmp_path)


@pytest.fixture
def seeded_client(client: TestClient, mbtiles_path: str) -> TestClient:
    """Client with a registered tileset."""
    client.post("/api/tilesets", json={
        "name": "test-region",
        "filepath": mbtiles_path,
        "format": "pbf",
        "description": "Test region tiles",
        "min_zoom": 0,
        "max_zoom": 14,
        "bounds": "-122.5,37.5,-122.0,38.0",
        "center_lat": 37.75,
        "center_lng": -122.25,
        "center_zoom": 10,
    })
    return client


# --- Health ---

def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


# --- Tilesets ---

def test_create_tileset(client: TestClient, mbtiles_path: str) -> None:
    resp = client.post("/api/tilesets", json={
        "name": "my-tiles",
        "filepath": mbtiles_path,
        "format": "pbf",
        "description": "My test tiles",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my-tiles"
    assert data["format"] == "pbf"
    assert data["description"] == "My test tiles"
    assert data["id"] is not None


def test_create_tileset_invalid_format(client: TestClient, mbtiles_path: str) -> None:
    resp = client.post("/api/tilesets", json={
        "name": "bad-format",
        "filepath": mbtiles_path,
        "format": "bmp",
    })
    assert resp.status_code == 400


def test_create_tileset_missing_file(client: TestClient) -> None:
    resp = client.post("/api/tilesets", json={
        "name": "missing",
        "filepath": "/nonexistent/path.mbtiles",
        "format": "pbf",
    })
    assert resp.status_code == 400


def test_create_tileset_duplicate_name(client: TestClient, mbtiles_path: str) -> None:
    client.post("/api/tilesets", json={
        "name": "dupe",
        "filepath": mbtiles_path,
        "format": "pbf",
    })
    resp = client.post("/api/tilesets", json={
        "name": "dupe",
        "filepath": mbtiles_path,
        "format": "pbf",
    })
    assert resp.status_code == 400


def test_list_tilesets(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/tilesets")
    assert resp.status_code == 200
    tilesets = resp.json()
    assert len(tilesets) == 1
    assert tilesets[0]["name"] == "test-region"


def test_get_tileset(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/tilesets/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "test-region"


def test_get_tileset_not_found(client: TestClient) -> None:
    resp = client.get("/api/tilesets/999")
    assert resp.status_code == 404


def test_update_tileset(seeded_client: TestClient) -> None:
    resp = seeded_client.put("/api/tilesets/1", json={
        "description": "Updated description",
        "max_zoom": 16,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Updated description"
    assert data["max_zoom"] == 16
    assert data["name"] == "test-region"


def test_update_tileset_not_found(client: TestClient) -> None:
    resp = client.put("/api/tilesets/999", json={"description": "nope"})
    assert resp.status_code == 404


def test_delete_tileset(seeded_client: TestClient) -> None:
    resp = seeded_client.delete("/api/tilesets/1")
    assert resp.status_code == 200
    resp = seeded_client.get("/api/tilesets/1")
    assert resp.status_code == 404


def test_delete_tileset_not_found(client: TestClient) -> None:
    resp = client.delete("/api/tilesets/999")
    assert resp.status_code == 404


# --- TileJSON ---

def test_tilejson(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/tilesets/1/tilejson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tilejson"] == "3.0.0"
    assert data["name"] == "test-region"
    assert data["minzoom"] == 0
    assert data["maxzoom"] == 14
    assert len(data["bounds"]) == 4
    assert len(data["center"]) == 3
    assert data["tiles"][0].startswith("/api/tiles/test-region/")


def test_tilejson_not_found(client: TestClient) -> None:
    resp = client.get("/api/tilesets/999/tilejson")
    assert resp.status_code == 404


# --- Tiles ---

def test_get_tile(tmp_path: Path, client: TestClient) -> None:
    # TMS y for z=1, y=0 is (2^1 - 1 - 0) = 1
    raw_data = b"fake pbf tile data"
    tile_data = gzip.compress(raw_data)
    mbtiles_path = _create_mbtiles(tmp_path / "tiles", [(1, 0, 1, tile_data)])

    client.post("/api/tilesets", json={
        "name": "tile-test",
        "filepath": mbtiles_path,
        "format": "pbf",
    })

    resp = client.get("/api/tiles/tile-test/1/0/0.pbf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/x-protobuf"
    # httpx auto-decompresses gzip, so we get the raw data back
    assert resp.content == raw_data


def test_get_tile_not_found_tileset(client: TestClient) -> None:
    resp = client.get("/api/tiles/nonexistent/0/0/0.pbf")
    assert resp.status_code == 404


def test_get_tile_not_found_tile(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/tiles/test-region/0/0/0.pbf")
    assert resp.status_code == 404


def test_get_tile_png(tmp_path: Path, client: TestClient) -> None:
    tile_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # fake PNG
    mbtiles_path = _create_mbtiles(tmp_path / "pngtiles", [(0, 0, 0, tile_data)])

    client.post("/api/tilesets", json={
        "name": "png-test",
        "filepath": mbtiles_path,
        "format": "png",
    })

    resp = client.get("/api/tiles/png-test/0/0/0.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert "content-encoding" not in resp.headers


# --- Styles ---

def test_list_styles(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/styles")
    assert resp.status_code == 200
    styles = resp.json()
    assert len(styles) == 1
    assert styles[0]["name"] == "test-region"
    assert styles[0]["url"] == "/api/styles/1"


def test_list_styles_empty(client: TestClient) -> None:
    resp = client.get("/api/styles")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_style_pbf(seeded_client: TestClient) -> None:
    resp = seeded_client.get("/api/styles/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == 8
    assert data["name"] == "test-region"
    assert "test-region" in data["sources"]
    source = data["sources"]["test-region"]
    assert source["type"] == "vector"
    assert source["minzoom"] == 0
    assert source["maxzoom"] == 14
    assert len(data["layers"]) >= 2


def test_get_style_raster(tmp_path: Path, client: TestClient) -> None:
    mbtiles_path = _create_mbtiles(tmp_path / "raster")
    client.post("/api/tilesets", json={
        "name": "raster-tiles",
        "filepath": mbtiles_path,
        "format": "png",
    })

    resp = client.get("/api/styles/1")
    assert resp.status_code == 200
    data = resp.json()
    source = data["sources"]["raster-tiles"]
    assert source["type"] == "raster"
    assert len(data["layers"]) == 1
    assert data["layers"][0]["type"] == "raster"


def test_get_style_not_found(client: TestClient) -> None:
    resp = client.get("/api/styles/999")
    assert resp.status_code == 404
