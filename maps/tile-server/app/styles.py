"""MapLibre style JSON router."""

from fastapi import APIRouter, HTTPException

from .database import query

router = APIRouter(prefix="/api/styles", tags=["styles"])


@router.get("")
def list_styles() -> list[dict]:
    """Return a style entry for each registered tileset."""
    tilesets = query("SELECT id, name, format, description FROM tilesets ORDER BY name")
    return [{"id": ts["id"], "name": ts["name"], "url": f"/api/styles/{ts['id']}"} for ts in tilesets]


@router.get("/{tileset_id}")
def get_style(tileset_id: int) -> dict:
    rows = query("SELECT * FROM tilesets WHERE id = ?", (tileset_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Tileset not found")

    ts = rows[0]
    bounds = [float(b) for b in ts["bounds"].split(",")]
    center = [ts["center_lng"], ts["center_lat"]]

    sources = {
        ts["name"]: {
            "type": "vector" if ts["format"] == "pbf" else "raster",
            "tiles": [f"/api/tiles/{ts['name']}/{{z}}/{{x}}/{{y}}.{ts['format']}"],
            "minzoom": ts["min_zoom"],
            "maxzoom": ts["max_zoom"],
            "bounds": bounds,
        }
    }

    if ts["format"] == "pbf":
        layers = [
            {
                "id": "background",
                "type": "background",
                "paint": {"background-color": "#1a1a2e"},
            },
            {
                "id": f"{ts['name']}-fill",
                "type": "fill",
                "source": ts["name"],
                "source-layer": "default",
                "paint": {"fill-color": "#2a2a4e", "fill-outline-color": "#4facfe"},
            },
        ]
    else:
        layers = [
            {
                "id": f"{ts['name']}-raster",
                "type": "raster",
                "source": ts["name"],
            },
        ]

    return {
        "version": 8,
        "name": ts["name"],
        "sources": sources,
        "layers": layers,
        "center": center,
        "zoom": ts["center_zoom"],
        "bearing": 0,
        "pitch": 0,
    }
