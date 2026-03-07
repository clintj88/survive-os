# SURVIVE OS - General Inventory

Categorized inventory management with barcode/QR support, consumption tracking,
stock alerts, location management, and full audit logging.

## Features

- **Categorized Items**: food, water, medical, tools, fuel, ammunition, building materials, trade goods
- **Barcode/QR Support**: Generate QR codes, scan-to-lookup workflow
- **Consumption Tracking**: Record usage, calculate rates, project days-of-supply
- **Stock Alerts**: Configurable thresholds, severity levels, Redis pub/sub notifications
- **Location Tracking**: Warehouses, caches, vehicles, buildings with transfer logging
- **Audit Log**: Immutable record of all inventory changes

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/api/items` | List/create items |
| GET/PUT/DELETE | `/api/items/{id}` | Get/update/delete item |
| POST | `/api/items/batch` | Batch import items |
| GET | `/api/scanning/qr/{id}` | Generate QR code PNG |
| GET | `/api/scanning/lookup?code=` | Lookup item by QR/barcode |
| POST | `/api/consumption` | Record consumption event |
| GET | `/api/consumption/history/{id}` | Consumption history |
| GET | `/api/consumption/rate/{id}` | Consumption rate + days-of-supply |
| GET | `/api/alerts` | Active stock alerts |
| POST | `/api/alerts/thresholds` | Set stock threshold |
| GET | `/api/locations` | List locations |
| POST | `/api/locations/transfer` | Transfer item between locations |
| GET | `/api/audit` | Query audit log |
| GET | `/api/audit/report` | Audit summary report |

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8050
```

## Testing

```bash
pytest tests/
```

## Configuration

Config file: `/etc/survive/inventory.yml`
Data directory: `/var/lib/survive/inventory/`
Port: 8050
