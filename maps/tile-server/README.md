# Tile Server - SURVIVE OS

Offline map tile server that manages and serves tiles from MBTiles files. Supports vector (PBF) and raster (PNG/JPG/WebP) tiles for MapLibre GL JS clients.

## Features

- Register and manage MBTiles tilesets with metadata
- Serve tiles via standard z/x/y URL scheme with TMS coordinate flipping
- TileJSON 3.0.0 metadata endpoint per tileset
- Auto-generated MapLibre GL Style Spec v8 styles (vector and raster)
- 24-hour browser caching with Cache-Control headers
- Gzip content encoding for PBF vector tiles

## API

### Tilesets
- `GET /health` - Health check
- `POST /api/tilesets` - Register MBTiles file
- `GET /api/tilesets` - List tilesets
- `GET /api/tilesets/{id}` - Get tileset metadata
- `PUT /api/tilesets/{id}` - Update tileset
- `DELETE /api/tilesets/{id}` - Unregister tileset
- `GET /api/tilesets/{id}/tilejson` - TileJSON 3.0.0 spec

### Tiles
- `GET /api/tiles/{tileset}/{z}/{x}/{y}.{ext}` - Serve tile (pbf, png, jpg, webp)

### Styles
- `GET /api/styles` - List available MapLibre styles
- `GET /api/styles/{tileset_id}` - Get MapLibre GL style for tileset

## Configuration

Copy `tile-server.yml` to `/etc/survive/tile-server.yml`. Port: 8060.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8060
```

## Testing

```bash
pytest tests/
```
