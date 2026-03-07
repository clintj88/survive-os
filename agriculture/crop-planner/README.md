# Crop Rotation Planner - SURVIVE OS Agriculture Module

Plan crop rotations, manage field plots, track companion planting compatibility,
and predict yields for post-infrastructure community farming.

## Features

- **Field Map & Plots**: Define fields as grids, assign crops per season
- **Rotation Schedules**: Four-year rotation templates (legume/leaf/fruit/root)
- **Companion Planting**: Database of beneficial and antagonistic crop pairings
- **Planting Calendar**: Frost-date-based sow/transplant/harvest windows
- **Yield Prediction**: Historical tracking with moving average predictions

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8030
```

## Configuration

Copy `crop-planner.yml` to `/etc/survive/crop-planner.yml` and adjust:
- `frost_dates`: Last spring / first fall frost dates (MM-DD)
- `climate_zone`: Your climate zone for rotation templates
- `redis.url`: Redis connection for weather observation integration

## API Endpoints

- `GET /health` - Health check
- `GET/POST /api/crops` - Crop management
- `GET/POST /api/fields` - Field management
- `GET /api/fields/{id}/plots` - Plot listing
- `POST /api/fields/{id}/plots/{pid}/assign` - Assign crop to plot
- `GET/POST /api/rotations/templates` - Rotation templates
- `GET /api/rotations/suggest/{plot_id}` - Next crop suggestion
- `GET/POST /api/companions` - Companion planting data
- `GET /api/companions/check` - Check crop compatibility
- `GET /api/calendar/frost-dates` - Frost date info
- `GET /api/calendar/planting-windows` - Planting windows
- `GET /api/calendar/month/{year}/{month}` - Monthly events
- `GET/POST /api/yields` - Yield records
- `GET /api/yields/predict` - Yield prediction

## Testing

```bash
pip install pytest httpx
pytest tests/
```

## Port: 8030
