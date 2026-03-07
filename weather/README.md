# SURVIVE OS - Weather Station

Offline-first weather monitoring, forecasting, and agricultural advisory system.

## Features

- **Manual Observations**: Record weather observations with full metadata
- **Sensor Ingestion**: Subscribe to automated sensor data via Redis pub/sub
- **Pattern Analysis**: Moving averages, pressure trends, simple rule-based forecasting
- **Planting Advisor**: Frost dates, growing season, planting window calculations
- **Storm Alerts**: Detect storms from pressure/wind/temperature and propagate alerts
- **Seasonal Trends**: Monthly/seasonal/annual aggregation, GDD, year-over-year comparison

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Configuration

Copy `weather.yml` to `/etc/survive/weather.yml` and adjust settings.

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/observations` - Weather observations CRUD
- `GET /api/forecast` - Current forecast
- `GET /api/analysis/averages` - Moving averages
- `GET /api/analysis/pressure` - Pressure trends
- `GET /api/planting/windows` - Planting windows
- `GET /api/storms/active` - Active storm alerts
- `GET /api/trends/monthly` - Monthly trend data

## Port

8080 (Weather)

## Testing

```bash
pytest tests/
```
