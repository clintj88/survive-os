# Map Annotations - SURVIVE OS

Collaborative map annotation system for marking geographic features — resource locations, hazard zones, agricultural plots, patrol routes, trade routes, and mesh network nodes.

## Features

- Layer-based annotation management (resource_locations, hazard_zones, agricultural_plots, patrol_routes, trade_routes, mesh_nodes)
- Bounding box spatial search with indexed lat/lng
- GeoJSON import/export for data interchange
- CRDT IDs on every annotation for distributed sync
- Cascading layer deletion

## API

- `GET /health` - Health check
- `POST /api/layers` - Create layer
- `GET /api/layers` - List layers with annotation counts
- `GET /api/layers/{id}` - Get layer
- `PUT /api/layers/{id}` - Update layer
- `DELETE /api/layers/{id}` - Delete layer and its annotations
- `POST /api/annotations` - Create annotation
- `GET /api/annotations` - List annotations (filter: `layer_id`)
- `GET /api/annotations/{id}` - Get annotation
- `GET /api/annotations/search` - Spatial search (`min_lat`, `min_lng`, `max_lat`, `max_lng`)
- `PUT /api/annotations/{id}` - Update annotation
- `DELETE /api/annotations/{id}` - Delete annotation
- `GET /api/geojson/export?layer_id=` - Export layer as GeoJSON FeatureCollection
- `POST /api/geojson/import?layer_id=` - Import GeoJSON features into layer

## Configuration

Copy `map-annotations.yml` to `/etc/survive/map-annotations.yml`. Port: 8061.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8061
```

## Testing

```bash
pytest tests/
```
