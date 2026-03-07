# Tool Library - SURVIVE OS Resources Module

Community tool lending library with inventory tracking, check-in/check-out,
maintenance scheduling, usage analytics, and reservations.

## Features

- **Tool Inventory**: Full CRUD with category/condition/availability filters
- **Check-In/Check-Out**: Borrow and return tools with condition tracking
- **Maintenance Scheduling**: Recurring tasks with overdue alerts
- **Usage & Wear Prediction**: Lifetime tracking and replacement planning
- **Reservations**: Future booking with conflict detection

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8050
```

## Configuration

Copy `tools.yml` to `/etc/survive/tools.yml` and adjust settings.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/api/tools` | List/create tools |
| GET/PUT/DELETE | `/api/tools/{id}` | Get/update/delete tool |
| POST | `/api/checkouts` | Check out a tool |
| POST | `/api/checkouts/{id}/checkin` | Return a tool |
| GET | `/api/checkouts/overdue` | Overdue checkouts |
| GET/POST | `/api/maintenance/tasks` | Maintenance tasks |
| POST | `/api/maintenance/tasks/{id}/complete` | Complete maintenance |
| GET | `/api/maintenance/overdue` | Overdue maintenance |
| GET | `/api/usage/stats/{id}` | Tool usage stats |
| GET | `/api/usage/wear/{id}` | Wear prediction |
| GET | `/api/usage/most-used` | Most used tools |
| GET/POST | `/api/reservations` | List/create reservations |
| GET | `/api/reservations/upcoming` | Upcoming reservations |

## Testing

```bash
pytest tests/
```

## Service

```bash
sudo cp survive-tools.service /etc/systemd/system/
sudo systemctl enable --now survive-tools
```
