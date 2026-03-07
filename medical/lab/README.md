# Lab Results - SURVIVE OS Medical

Laboratory information system for managing test catalogs, panels, orders, and results with automatic interpretation and alerting.

## Features

- Test catalog with reference ranges and critical thresholds
- Lab panels (pre-defined test groupings, e.g., CBC, BMP)
- Order workflow: ordered → collected → processing → completed (with cancellation)
- Auto-interpretation of results (normal, abnormal, critical_low, critical_high)
- Abnormal/critical result alerts
- Patient result trend tracking over time
- Pre-seeded with 18 common lab tests and 2 panels (CBC, BMP)
- Optional SQLCipher encryption at rest
- Role-based access: requires `X-Role: medical` header

## API

### Test Catalog
- `GET /health` - Health check
- `GET /api/catalog` - List tests (filter: `active`, `specimen_type`)
- `GET /api/catalog/{id}` - Get test
- `POST /api/catalog` - Create test
- `PUT /api/catalog/{id}` - Update test
- `DELETE /api/catalog/{id}` - Delete test

### Panels
- `GET /api/panels` - List panels with tests
- `GET /api/panels/{id}` - Get panel with tests
- `POST /api/panels` - Create panel
- `PUT /api/panels/{id}` - Update panel
- `DELETE /api/panels/{id}` - Delete panel

### Orders
- `GET /api/orders` - List orders (filter: `patient_id`, `status`)
- `GET /api/orders/{id}` - Get order
- `POST /api/orders` - Create order (single test or panel)
- `PUT /api/orders/{id}/status` - Update order status

### Results
- `POST /api/results` - Record result (auto-interprets, auto-completes order)
- `GET /api/results/alerts` - Abnormal/critical results (filter: `patient_id`)
- `GET /api/results/trends/{patient_id}/{test_id}` - Result trends over time
- `GET /api/results/patient/{patient_id}` - Patient results (filter: `test_id`, `date_from`, `date_to`)

## Configuration

Copy `lab.yml` to `/etc/survive/lab.yml`. Port: 8042.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8042
```

## Testing

```bash
pytest tests/
```
