"""Tile serving router - reads tiles from MBTiles files."""

import sqlite3

from fastapi import APIRouter, HTTPException, Response

from .database import query

router = APIRouter(prefix="/api/tiles", tags=["tiles"])


def _flip_y(z: int, y: int) -> int:
    """Convert XYZ tile y to TMS y (MBTiles uses TMS scheme)."""
    return (1 << z) - 1 - y


CONTENT_TYPES = {
    "pbf": "application/x-protobuf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "webp": "image/webp",
}


@router.get("/{tileset}/{z}/{x}/{y}.{ext}")
def get_tile(tileset: str, z: int, x: int, y: int, ext: str) -> Response:
    rows = query("SELECT filepath, format FROM tilesets WHERE name = ?", (tileset,))
    if not rows:
        raise HTTPException(status_code=404, detail="Tileset not found")

    ts = rows[0]
    tms_y = _flip_y(z, y)

    try:
        conn = sqlite3.connect(f"file:{ts['filepath']}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            (z, x, tms_y),
        ).fetchone()
        conn.close()
    except sqlite3.OperationalError:
        raise HTTPException(status_code=500, detail="Cannot read MBTiles file")

    if not row:
        raise HTTPException(status_code=404, detail="Tile not found")

    content_type = CONTENT_TYPES.get(ts["format"], "application/octet-stream")
    headers = {"Cache-Control": "public, max-age=86400"}
    if ts["format"] == "pbf":
        headers["Content-Encoding"] = "gzip"

    return Response(content=row[0], media_type=content_type, headers=headers)
