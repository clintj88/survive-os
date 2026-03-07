# Drone Aerial Maps - SURVIVE OS

Drone survey management and orthomosaic processing for aerial mapping, terrain models, and change detection between temporal surveys.

## Features

- Drone survey mission tracking with metadata (operator, drone model, area bounds)
- Aerial image registration with geolocation (lat/lng/altitude)
- Orthomosaic processing jobs with status tracking (pending → processing → completed)
- Change detection between surveys (new_construction, crop_changes, erosion, water_level)
- Terrain model / DEM metadata management
- Survey comparison endpoint

## API

### Surveys
- `GET /health` - Health check
- `POST /api/surveys` - Create survey
- `GET /api/surveys` - List surveys (filter: `status`, `area_name`)
- `GET /api/surveys/{id}` - Get survey
- `PUT /api/surveys/{id}` - Update survey
- `DELETE /api/surveys/{id}` - Delete survey (cascades)
- `GET /api/surveys/{id}/compare/{other_id}` - Compare two surveys

### Images
- `POST /api/images` - Register drone image
- `GET /api/images` - List images (filter: `survey_id`)
- `GET /api/images/{id}` - Get image
- `DELETE /api/images/{id}` - Delete image record

### Processing
- `POST /api/processing` - Create processing job
- `GET /api/processing` - List jobs (filter: `survey_id`, `status`)
- `GET /api/processing/{id}` - Get job
- `PUT /api/processing/{id}` - Update job status
- `POST /api/processing/{id}/run` - Execute processing (stub)

### Change Detection
- `POST /api/changes` - Record detected change
- `GET /api/changes` - List changes (filter: `survey_a_id`, `survey_b_id`)
- `GET /api/changes/{id}` - Get change
- `DELETE /api/changes/{id}` - Delete change

### Terrain Models
- `POST /api/terrain` - Register terrain model
- `GET /api/terrain` - List terrain models (filter: `survey_id`)
- `GET /api/terrain/{id}` - Get terrain model
- `DELETE /api/terrain/{id}` - Delete terrain model

## Configuration

Copy `drone-maps.yml` to `/etc/survive/drone-maps.yml`. Port: 8062.

## Running

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8062
```

## Testing

```bash
pytest tests/
```
