# Engineering & Maintenance - SURVIVE OS

Preventive maintenance scheduling, parts cross-reference, construction calculators, chemistry recipes, technical guides, and drawing management for post-infrastructure communities.

## Features

- **Preventive Maintenance**: Track infrastructure items, schedule recurring maintenance, log completion history
- **Parts Cross-Reference**: Find compatible parts across equipment, identify salvage sources
- **Construction Calculator**: Lumber, concrete, roofing, fencing, and paint calculators
- **Chemistry Recipes**: Practical recipes for soap, fuel, preservation, water treatment, and more
- **Technical Guides**: Step-by-step guides for solar, radio, plumbing, drone operations
- **Technical Drawings**: Upload and manage technical drawing metadata

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8050
```

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/maintenance/items` - Infrastructure items
- `GET/POST /api/maintenance/schedules` - Maintenance schedules
- `GET /api/maintenance/overdue` - Overdue maintenance alerts
- `GET/POST /api/parts` - Parts inventory
- `GET /api/parts/search?equipment=` - Parts search
- `GET /api/parts/cross-reference` - Cross-reference parts
- `POST /api/calculator/{type}` - Construction calculators
- `GET/POST /api/chemistry` - Chemistry recipes
- `GET/POST /api/guides` - Technical guides
- `GET/POST /api/drawings` - Technical drawings

## Configuration

Copy `engineering.yml` to `/etc/survive/engineering.yml` and adjust as needed.

## Port

8050 (Resources/Inventory)
