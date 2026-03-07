# Livestock Management - SURVIVE OS

Offline-first livestock management module for tracking animals, breeding, feed, veterinary care, and production records.

## Features

- **Animal Records**: Individual tracking with pedigree/lineage views
- **Breeding Planner**: Inbreeding coefficient calculator (Wright's method), gestation tracking, optimal pairing suggestions
- **Feed Calculator**: Species-specific requirements by production stage, inventory tracking with low-stock alerts
- **Veterinary Log**: Treatment records, medication inventory, withdrawal period tracking, vaccination schedules
- **Production Records**: Milk, eggs, weight, wool tracking with analytics and feed conversion ratios

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8030
```

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/animals` - Animal CRUD
- `GET /api/animals/{id}/pedigree` - Pedigree tree
- `GET/POST /api/breeding/events` - Breeding events
- `GET /api/breeding/inbreeding?sire_id=&dam_id=` - Inbreeding check
- `GET /api/breeding/suggestions` - Optimal pairings
- `GET /api/feed/calculate?species=&weight_kg=&production_stage=` - Feed calculator
- `GET /api/feed/inventory/alerts` - Low feed alerts
- `GET/POST /api/vet/treatments` - Treatment log
- `GET /api/vet/withdrawals` - Active withdrawal periods
- `GET/POST /api/production/records` - Production tracking
- `GET /api/production/analytics?type=` - Production analytics
- `GET /api/production/fcr?animal_id=` - Feed conversion ratio

## Configuration

Copy `livestock.yml` to `/etc/survive/livestock.yml` and adjust as needed.

## Port

8030 (Agriculture subsystem)
