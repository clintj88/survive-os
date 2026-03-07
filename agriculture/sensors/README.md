# Sensor Integration - SURVIVE OS Agriculture

ESP32 sensor node registry and data ingestion via Meshtastic mesh network.

## Features

- **Node Registry**: Register/discover ESP32 sensor nodes with health monitoring
- **Data Ingestion**: Subscribe to Meshtastic mesh messages via Redis pub/sub
- **Sensor Types**: Soil moisture, weather (temp/humidity/pressure), rain gauge
- **Frost Alerts**: Configurable temperature threshold with trend detection
- **Data Feeds**: Publish aggregated weather data for other modules
- **Historical Queries**: Time-range queries with hourly/daily aggregation
- **CSV Export**: Download sensor data as CSV

## Configuration

Copy `sensors.yml` to `/etc/survive/sensors.yml` and adjust settings.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/nodes` | GET/POST | List/create sensor nodes |
| `/api/nodes/{id}` | GET/PUT/DELETE | Node CRUD |
| `/api/dashboard` | GET | Latest readings from all nodes |
| `/api/readings/{type}` | GET | Historical data (soil/weather/rain) |
| `/api/readings/{type}/csv` | GET | CSV export |
| `/api/alerts/frost` | GET | Frost alert history |

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8030
```

## Service

```bash
sudo cp survive-sensors.service /etc/systemd/system/
sudo systemctl enable --now survive-sensors
```
