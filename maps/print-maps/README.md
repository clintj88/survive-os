# Printable Maps - SURVIVE OS

Printable map generation service for creating custom map PDFs/PNGs with configurable paper sizes, orientations, overlays, and reusable templates.

## Features

- Print job creation with immediate rendering
- Paper sizes: A4, A3, letter, tabloid, custom dimensions
- Orientations: portrait, landscape
- DPI options: 150, 300, 600
- Overlay layers, legend, scale bar, north arrow, grid, date toggles
- Reusable print templates (patrol_map, foraging_map, trade_route_map, general)
- Job status tracking and file download

## API

### Print Jobs
- `GET /health` - Health check
- `POST /api/jobs` - Create and render print job
- `GET /api/jobs` - List jobs (filter: `status`, `date_from`, `date_to`)
- `GET /api/jobs/{id}` - Get job
- `DELETE /api/jobs/{id}` - Delete job and output file
- `GET /api/jobs/{id}/download` - Download rendered map PNG

### Print Templates
- `POST /api/templates` - Create template
- `GET /api/templates` - List templates (filter: `template_type`)
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

## Configuration

Copy `print-maps.yml` to `/etc/survive/print-maps.yml`. Port: 8063.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8063
```

## Testing

```bash
pytest tests/
```
