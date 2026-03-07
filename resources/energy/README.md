# Energy & Fuel Tracking - SURVIVE OS

Monitors solar panels, battery banks, fuel reserves, generators, and power budgets for off-grid communities.

## Features

- **Solar Panel Monitoring**: Track panel output, daily/weekly production, efficiency vs rated watts
- **Battery Bank Tracking**: State-of-charge logging, charge/discharge cycles, health estimation
- **Fuel Reserves**: Multi-fuel inventory (gasoline, diesel, propane, firewood, kerosene, ethanol), consumption logging, days-of-supply projection
- **Generator Management**: Runtime logging, fuel efficiency, maintenance scheduling
- **Power Budget Calculator**: Load tracking by priority, demand vs supply analysis, load-shedding recommendations

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8050
```

## API Endpoints

| Prefix | Description |
|---|---|
| `GET /health` | Health check |
| `/api/solar/*` | Solar panel CRUD, output logging, production, efficiency |
| `/api/batteries/*` | Battery bank CRUD, state logging, cycles, low-battery alerts |
| `/api/fuel/*` | Fuel storage/consumption CRUD, summary, days-of-supply, low-fuel alerts |
| `/api/generators/*` | Generator CRUD, runtime, efficiency, maintenance scheduling |
| `/api/budget/*` | Power load CRUD, demand/supply calculation, load-shedding |

## Configuration

Config file: `/etc/survive/energy.yml`

## Data Storage

SQLite database at `/var/lib/survive/energy/energy.db`

## Testing

```bash
pytest tests/
```
